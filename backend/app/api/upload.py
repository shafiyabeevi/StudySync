"""
Document upload API endpoint.
Handles file upload, validation, text extraction, chunking, and embedding.
"""
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
from app.core.config import get_settings
from app.core.local_db import get_db, STORAGE_DIR
from app.services.parser import extract_text
from app.services.chunker import chunk_text
from app.services.vector_store import store_chunks
from app.schemas.models import DocumentUploadResponse, ErrorResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}},
)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF or DOCX document for processing.
    Extracts text, chunks it, generates embeddings, and stores in ChromaDB.
    """
    settings = get_settings()

    # ── Validate file type ──
    filename = file.filename or "unknown"
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF (.pdf) and Word (.docx) files are accepted."
        )

    # ── Read and validate file size ──
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File size ({size_mb:.1f} MB) exceeds the {settings.MAX_FILE_SIZE_MB}MB limit. Please upload a smaller file."
        )

    # ── Generate document ID ──
    doc_id = str(uuid.uuid4())

    try:
        # ── Extract text ──
        extracted_text = extract_text(file_bytes, filename)

        # ── Store file locally ──
        file_type = "pdf" if ext == ".pdf" else "docx"
        doc_dir = os.path.join(STORAGE_DIR, doc_id)
        os.makedirs(doc_dir, exist_ok=True)
        storage_path = os.path.join(doc_dir, filename)
        
        with open(storage_path, "wb") as f:
            f.write(file_bytes)

        # ── Save document record to Local DB ──
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO documents 
            (id, user_id, filename, file_path, file_type, file_size, extracted_text, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            doc_id, 
            settings.DEFAULT_USER_ID, 
            filename, 
            storage_path, 
            file_type, 
            file_size, 
            extracted_text, 
            'processing'
        ))
        conn.commit()

        # ── Chunk and embed ──
        chunks = chunk_text(extracted_text)
        num_stored = store_chunks(doc_id, chunks)

        # ── Update status to ready ──
        cursor.execute('UPDATE documents SET status = ? WHERE id = ?', ('ready', doc_id))
        conn.commit()
        conn.close()

        return DocumentUploadResponse(
            id=doc_id,
            filename=filename,
            status="ready",
            message=f"Document processed successfully. Extracted {len(extracted_text)} characters, created {num_stored} searchable chunks."
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        try:
            conn = get_db()
            conn.execute('UPDATE documents SET status = ? WHERE id = ?', ('error', doc_id))
            conn.commit()
            conn.close()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
