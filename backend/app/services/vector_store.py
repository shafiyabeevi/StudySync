"""
ChromaDB vector store service.
Handles embedding storage and retrieval for RAG.
"""
import os
import logging
import threading

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import get_settings
from app.services.chunker import chunk_text

logger = logging.getLogger(__name__)

_embedding_model = None
_vector_stores: dict[str, Chroma] = {}
_store_locks: dict[str, threading.RLock] = {}
_store_locks_guard = threading.Lock()


def _get_store_lock(document_id: str) -> threading.RLock:
    with _store_locks_guard:
        if document_id not in _store_locks:
            _store_locks[document_id] = threading.RLock()
        return _store_locks[document_id]


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Get or create the Gemini embedding model (singleton)."""
    global _embedding_model
    if _embedding_model is None:
        settings = get_settings()
        os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
        _embedding_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )
    return _embedding_model


def _get_chroma_store(document_id: str) -> Chroma:
    """Get or create a ChromaDB collection for a specific document."""
    if document_id not in _vector_stores:
        settings = get_settings()
        persist_dir = os.path.join(settings.CHROMA_PERSIST_DIR, document_id)
        _vector_stores[document_id] = Chroma(
            collection_name=f"doc_{document_id}",
            embedding_function=_get_embeddings(),
            persist_directory=persist_dir,
        )
    return _vector_stores[document_id]


def store_chunks(document_id: str, chunks: list[str]) -> int:
    """
    Embed and store text chunks in ChromaDB for a document.
    Returns the number of chunks stored.
    """
    if not chunks:
        return 0

    store = _get_chroma_store(document_id)

    # Add metadata to each chunk
    metadatas = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]
    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

    store.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
    logger.info(f"Stored {len(chunks)} chunks for document {document_id}")
    return len(chunks)


def ensure_document_store(document_id: str, extracted_text: str | None) -> bool:
    """Ensure a document collection exists, rebuilding it from Supabase text if empty."""
    if not document_id:
        return False
    text = str(extracted_text or "").strip()
    if not text:
        logger.warning("Cannot rebuild Chroma store for %s: extracted text is empty", document_id)
        return False

    lock = _get_store_lock(document_id)
    with lock:
        try:
            store = _get_chroma_store(document_id)
            if store.count() > 0:
                return True

            chunks = chunk_text(text)
            if not chunks:
                logger.warning("Cannot rebuild Chroma store for %s: chunking returned no chunks", document_id)
                return False

            num_stored = store_chunks(document_id, chunks)
            if num_stored == 0:
                return False
            logger.info("Rebuilt Chroma store for document %s with %d chunks", document_id, num_stored)
            return True
        except Exception as exc:
            logger.error("Failed to rebuild Chroma store for document %s: %s", document_id, exc)
            return False


def retrieve_relevant_chunks(
    document_id: str,
    query: str,
    top_k: int = 5,
    extracted_text: str | None = None,
) -> list[str]:
    """
    Retrieve the most relevant chunks for a query from a document's collection.
    Returns a list of text chunks sorted by relevance.
    """
    try:
        chunks_with_ids = retrieve_relevant_chunks_with_ids(
            document_id, query, top_k=top_k, extracted_text=extracted_text
        )
        return [item["text"] for item in chunks_with_ids]
    except Exception as e:
        logger.error(f"Retrieval error for document {document_id}: {e}")
        return []


def retrieve_relevant_chunks_with_ids(
    document_id: str,
    query: str,
    top_k: int = 5,
    extracted_text: str | None = None,
) -> list[dict]:
    """Retrieve relevant chunks and include lightweight metadata for downstream features."""
    if extracted_text is not None:
        ensure_document_store(document_id, extracted_text)
    store = _get_chroma_store(document_id)

    try:
        results = store.similarity_search(query, k=top_k)
        chunks = []
        for index, doc in enumerate(results):
            metadata = getattr(doc, "metadata", {}) or {}
            chunk_id = metadata.get("chunk_id") or metadata.get("id") or f"{document_id}_chunk_{index}"
            chunks.append({"text": doc.page_content, "id": chunk_id})
        logger.info(f"Retrieved {len(chunks)} chunks for query on document {document_id}")
        return chunks
    except Exception as e:
        logger.error(f"Retrieval error for document {document_id}: {e}")
        return []


def delete_document_store(document_id: str):
    """Remove a document's vector store (cleanup)."""
    if document_id in _vector_stores:
        del _vector_stores[document_id]
    settings = get_settings()
    persist_dir = os.path.join(settings.CHROMA_PERSIST_DIR, document_id)
    if os.path.exists(persist_dir):
        import shutil
        shutil.rmtree(persist_dir)
        logger.info(f"Removed chroma persist dir for document {document_id}")
