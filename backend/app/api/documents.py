"""
Document listing and exam notes API endpoints.
"""
from fastapi import APIRouter, HTTPException
import json
import os
from app.core.config import get_settings
from app.core.local_db import get_db
from app.services.notes_generator import generate_exam_notes
from app.services.vector_store import delete_document_store
from app.schemas.models import DocumentListResponse, DocumentInfo, ExamNotesResponse, ErrorResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def _load_cached_notes(raw_value):
    """Safely parse cached exam notes from the database."""
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


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents for the current user."""
    settings = get_settings()

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, filename, file_type, file_size, status, created_at, exam_notes 
            FROM documents 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (settings.DEFAULT_USER_ID,))
        
        rows = cursor.fetchall()
        conn.close()

        documents = []
        for doc in rows:
            documents.append(DocumentInfo(
                id=doc["id"],
                filename=doc["filename"],
                file_type=doc["file_type"],
                file_size=doc["file_size"],
                status=doc["status"],
                created_at=doc["created_at"],
                has_notes=doc["exam_notes"] is not None,
            ))

        return DocumentListResponse(documents=documents)
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to load documents.")


@router.get(
    "/documents/{document_id}/notes",
    response_model=ExamNotesResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_exam_notes(document_id: str):
    """
    Get exam notes for a document.
    If notes haven't been generated yet, generates them on-demand and caches in DB.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, filename, extracted_text, exam_notes, status FROM documents WHERE id = ?', (document_id,))
        row = cursor.fetchone()
    except Exception as e:
        logger.error(f"DB query failed: {e}")
        raise HTTPException(status_code=500, detail="Database error.")

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = dict(row)

    if doc["status"] != "ready":
        conn.close()
        return ExamNotesResponse(
            document_id=document_id,
            filename=doc["filename"],
            notes=None,
            status=doc["status"],
            message="Document is still being processed. Please wait."
        )

    # Return cached notes if available
    cached_notes = _load_cached_notes(doc.get("exam_notes"))
    if cached_notes is not None:
        conn.close()
        return ExamNotesResponse(
            document_id=document_id,
            filename=doc["filename"],
            notes=cached_notes,
            status="ready",
        )

    # Generate notes on demand
    try:
        notes = await generate_exam_notes(doc["extracted_text"], doc["filename"])

        # Cache in DB
        cursor.execute('UPDATE documents SET exam_notes = ? WHERE id = ?', (json.dumps(notes, ensure_ascii=False), document_id))
        conn.commit()
        conn.close()

        return ExamNotesResponse(
            document_id=document_id,
            filename=doc["filename"],
            notes=notes,
            status="ready",
        )
    except ValueError as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        conn.close()
        logger.error(f"Notes generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate exam notes. Please try again.")


@router.get("/documents/{document_id}/text")
async def get_document_text(document_id: str):
    """Get the extracted text of a document."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, filename, extracted_text, status FROM documents WHERE id = ?', (document_id,))
        row = cursor.fetchone()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error.")

    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc = dict(row)
    return {
        "document_id": doc["id"],
        "filename": doc["filename"],
        "text": doc["extracted_text"],
        "status": doc["status"],
    }



@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all dependent data (storage, vector store, DB rows, feedback).

    This performs the following steps:
    - remove stored file from local storage (or Supabase if configured)
    - remove chroma vector store persist directory
    - delete rows referencing the document from teach_it_back_attempts, chunk_doubt_counts, feedback
    - delete the document row from documents
    """
    settings = get_settings()

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, filename, file_path FROM documents WHERE id = ?', (document_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Document not found.")

        doc = dict(row)

        # 1) Remove file from local storage if exists
        try:
            file_path = doc.get('file_path')
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to remove file {file_path}: {e}")

        # 2) Remove Chroma vector store persist dir
        try:
            delete_document_store(document_id)
        except Exception as e:
            logger.warning(f"Failed to delete chroma store for {document_id}: {e}")

        # 3) Remove DB rows referencing this document
        try:
            cursor.execute('DELETE FROM teach_it_back_attempts WHERE document_id = ?', (document_id,))
            cursor.execute('DELETE FROM chunk_doubt_counts WHERE document_id = ?', (document_id,))
            cursor.execute('DELETE FROM feedback WHERE reference_id = ?', (document_id,))
            cursor.execute('DELETE FROM documents WHERE id = ?', (document_id,))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to delete DB rows for document {document_id}: {e}")
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=500, detail="Failed to delete document data.")

        conn.close()

        return {"status": "ok", "message": "Document deleted."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Document deletion failed.")


