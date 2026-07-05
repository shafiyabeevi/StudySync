import hashlib
import logging
import re
from app.core.local_db import get_db

logger = logging.getLogger(__name__)


def _chunk_key(document_id: str, chunk_text: str) -> str:
    return hashlib.sha256(f"{document_id}:{chunk_text}".encode("utf-8")).hexdigest()


def log_doubt_question(document_id: str, chunk_text: str, chunk_id: str | None = None) -> None:
    if not chunk_text or not chunk_text.strip():
        return

    key = chunk_id or _chunk_key(document_id, chunk_text)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO chunk_doubt_counts (chunk_hash, document_id, doubt_count, chunk_text)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(chunk_hash) DO UPDATE SET
            doubt_count = doubt_count + 1,
            last_updated = CURRENT_TIMESTAMP,
            chunk_text = excluded.chunk_text
        """,
        (key, document_id, chunk_text),
    )
    conn.commit()
    conn.close()


def get_document_heatmap(document_id: str, document_text: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT chunk_hash, document_id, doubt_count, chunk_text
        FROM chunk_doubt_counts
        WHERE document_id = ?
        ORDER BY doubt_count DESC
        """,
        (document_id,),
    ).fetchall()
    conn.close()

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", document_text or "") if p and p.strip()]
    if not paragraphs:
        paragraphs = [document_text.strip()] if document_text and document_text.strip() else []

    max_doubt = max((int(row["doubt_count"] or 0) for row in rows), default=1)
    paragraph_scores = []

    for index, paragraph in enumerate(paragraphs):
        best_score = 0
        for row in rows:
            chunk_text = row["chunk_text"] or ""
            if not chunk_text:
                continue
            if _token_overlap(paragraph, chunk_text) > 0.12:
                confidence = _token_overlap(paragraph, chunk_text) * (int(row["doubt_count"] or 0) / max_doubt)
                best_score = max(best_score, confidence)

        score_percent = int(min(100, max(0, round(best_score * 100))))
        paragraph_scores.append({
            "index": index,
            "text": paragraph,
            "score_percent": score_percent,
            "snippet": paragraph[:140],
        })

    top_paragraphs = [item for item in paragraph_scores if item["score_percent"] > 0][:3]
    return {
        "document_id": document_id,
        "paragraphs": paragraph_scores,
        "top_paragraphs": top_paragraphs,
    }


def _token_overlap(left: str, right: str) -> float:
    tokens_left = set(re.findall(r"\w+", left.lower()))
    tokens_right = set(re.findall(r"\w+", right.lower()))
    if not tokens_left or not tokens_right:
        return 0.0
    return len(tokens_left & tokens_right) / max(1, len(tokens_left | tokens_right))
