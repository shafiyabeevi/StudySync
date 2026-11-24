"""
Document listing, text, deletion, and exam notes API endpoints.
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import get_settings
from app.core.documents import get_owned_document
from app.core.supabase_client import get_supabase
from app.core.supabase_storage import (
    SupabaseStorageError,
    delete_storage_object,
    download_storage_object,
    upload_storage_object,
)
from app.schemas.models import (
    DocumentInfo,
    DocumentListResponse,
    ErrorResponse,
    ExamNotesResponse,
)
from app.services.notes_generator import generate_exam_notes
from app.services.vector_store import delete_document_store

logger = logging.getLogger(__name__)
router = APIRouter()


def _load_cached_notes(raw_value):
    if raw_value is None:
        return None
    if isinstance(raw_value, (dict, list)):
        return raw_value
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
        except (json.JSONDecodeError, TypeError):
            return None
        if isinstance(parsed, (dict, list)):
            return parsed
    return None


def _document_or_404(supabase, user: AuthenticatedUser, document_id: str) -> dict:
    document = get_owned_document(supabase, user.id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return document


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(user: AuthenticatedUser = Depends(get_current_user)):
    try:
        response = (
            get_supabase(user.access_token)
            .table("documents")
            .select("id,filename,file_type,file_size,status,created_at,exam_notes")
            .eq("user_id", user.id)
            .order("created_at", desc=True)
            .execute()
        )
        documents = [
            DocumentInfo(
                id=doc["id"],
                filename=doc["filename"],
                file_type=doc["file_type"],
                file_size=doc["file_size"],
                status=doc["status"],
                created_at=doc["created_at"],
                has_notes=doc["exam_notes"] is not None,
            )
            for doc in response.data
        ]
        return DocumentListResponse(documents=documents)
    except Exception as exc:
        logger.error("Failed to list documents for user %s: %s", user.id, exc)
        raise HTTPException(status_code=500, detail="Failed to load documents.") from exc


@router.get(
    "/documents/{document_id}/notes",
    response_model=ExamNotesResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_exam_notes(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    supabase = get_supabase(user.access_token)
    try:
        doc = _document_or_404(supabase, user, document_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Document lookup failed for %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail="Database error.") from exc

    if doc["status"] != "ready":
        return ExamNotesResponse(
            document_id=document_id,
            filename=doc["filename"],
            notes=None,
            status=doc["status"],
            message="Document is still being processed. Please wait.",
        )

    cached_notes = _load_cached_notes(doc.get("exam_notes"))
    if cached_notes is not None:
        return ExamNotesResponse(
            document_id=document_id,
            filename=doc["filename"],
            notes=cached_notes,
            status="ready",
        )

    try:
        notes = await generate_exam_notes(doc.get("extracted_text") or "", doc["filename"])
        supabase.table("documents").update({"exam_notes": notes}).eq(
            "id", doc["id"]
        ).eq("user_id", user.id).execute()
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Notes generation or persistence failed for %s: %s", document_id, exc)
        raise HTTPException(
            status_code=500, detail="Failed to generate exam notes. Please try again."
        ) from exc

    return ExamNotesResponse(
        document_id=document_id,
        filename=doc["filename"],
        notes=notes,
        status="ready",
    )


@router.get("/documents/{document_id}/text")
async def get_document_text(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        doc = _document_or_404(get_supabase(user.access_token), user, document_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Document text lookup failed for %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail="Database error.") from exc

    return {
        "document_id": doc["id"],
        "filename": doc["filename"],
        "text": doc.get("extracted_text"),
        "status": doc["status"],
    }


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
):
    settings = get_settings()
    supabase = get_supabase(user.access_token)
    try:
        doc = _document_or_404(supabase, user, document_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Document lookup failed before deletion for %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail="Document deletion failed.") from exc

    object_path = doc.get("file_path")
    if not object_path:
        raise HTTPException(status_code=409, detail="Document has no Storage object path.")

    try:
        file_bytes = await download_storage_object(
            user.access_token, settings.SUPABASE_STORAGE_BUCKET, object_path
        )
        await delete_storage_object(
            user.access_token, settings.SUPABASE_STORAGE_BUCKET, object_path
        )
    except SupabaseStorageError as exc:
        logger.error("Could not remove Storage object for document %s: %s", document_id, exc)
        raise HTTPException(status_code=502, detail="Failed to remove the document file.") from exc

    try:
        deleted = supabase.table("documents").delete().eq("id", doc["id"]).eq(
            "user_id", user.id
        ).select("id").execute().data
        if not deleted:
            raise RuntimeError("Document row was not deleted.")
    except Exception as exc:
        try:
            await upload_storage_object(
                user.access_token,
                settings.SUPABASE_STORAGE_BUCKET,
                object_path,
                file_bytes,
                (
                    "application/pdf"
                    if doc["file_type"] == "pdf"
                    else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ),
            )
        except SupabaseStorageError as compensation_exc:
            logger.critical(
                "Failed to restore Storage object %s after metadata deletion failed: %s",
                object_path,
                compensation_exc,
            )
        logger.error("Failed to delete document metadata for %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail="Failed to delete document metadata.") from exc

    try:
        delete_document_store(doc["id"])
    except Exception as exc:
        logger.error("Failed to remove Chroma store for document %s: %s", document_id, exc)
        raise HTTPException(
            status_code=500, detail="Document data was deleted, but vector cleanup failed."
        ) from exc

    return {"status": "ok", "message": "Document deleted."}
