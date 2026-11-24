"""
Document upload API endpoint.
Handles authenticated Supabase Storage uploads and Chroma indexing.
"""
import logging
import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import get_settings
from app.core.supabase_client import get_supabase
from app.core.supabase_storage import (
    SupabaseStorageError,
    delete_storage_object,
    upload_storage_object,
)
from app.schemas.models import DocumentUploadResponse, ErrorResponse
from app.services.chunker import chunk_text
from app.services.parser import extract_text
from app.services.vector_store import store_chunks

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}},
)
async def upload_document(
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    settings = get_settings()

    original_filename = file.filename or "unknown"
    filename = original_filename.replace("\\", "/").rsplit("/", 1)[-1]
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF (.pdf) and Word (.docx) files are accepted.",
        )

    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File size ({size_mb:.1f} MB) exceeds the {settings.MAX_FILE_SIZE_MB}MB limit. Please upload a smaller file.",
        )

    document_id = str(uuid.uuid4())
    object_path = f"{user.id}/{document_id}/{filename}"
    content_type = "application/pdf" if ext == ".pdf" else (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    try:
        extracted_text = extract_text(file_bytes, filename)
        await upload_storage_object(
            user.access_token,
            settings.SUPABASE_STORAGE_BUCKET,
            object_path,
            file_bytes,
            content_type,
        )
    except SupabaseStorageError as exc:
        logger.error("Supabase Storage upload failed for document %s: %s", document_id, exc)
        raise HTTPException(status_code=502, detail="Failed to store the uploaded document.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    supabase = get_supabase(user.access_token)
    try:
        supabase.table("documents").insert({
            "id": document_id,
            "user_id": user.id,
            "filename": filename,
            "file_path": object_path,
            "file_type": ext[1:],
            "file_size": file_size,
            "extracted_text": extracted_text,
            "status": "processing",
        }).execute()
    except Exception as exc:
        try:
            await delete_storage_object(
                user.access_token, settings.SUPABASE_STORAGE_BUCKET, object_path
            )
        except SupabaseStorageError as cleanup_exc:
            logger.error(
                "Could not remove orphaned Storage object %s after metadata insertion failed: %s",
                object_path,
                cleanup_exc,
            )
        logger.error("Document metadata insertion failed for %s: %s", document_id, exc)
        raise HTTPException(status_code=500, detail="Failed to save document metadata.") from exc

    try:
        chunks = chunk_text(extracted_text)
        num_stored = store_chunks(document_id, chunks)
        supabase.table("documents").update({"status": "ready"}).eq(
            "id", document_id
        ).eq("user_id", user.id).execute()
    except Exception as exc:
        try:
            supabase.table("documents").update({"status": "error"}).eq(
                "id", document_id
            ).eq("user_id", user.id).execute()
        except Exception as status_exc:
            logger.error("Could not mark document %s as errored: %s", document_id, status_exc)
        logger.error("Upload processing failed for document %s: %s", document_id, exc)
        raise HTTPException(
            status_code=500, detail=f"Failed to process document: {exc}"
        ) from exc

    return DocumentUploadResponse(
        id=document_id,
        filename=filename,
        status="ready",
        message=f"Document processed successfully. Extracted {len(extracted_text)} characters, created {num_stored} searchable chunks.",
    )
