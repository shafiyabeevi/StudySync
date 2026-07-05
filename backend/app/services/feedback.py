import logging
from app.core.local_db import get_db

logger = logging.getLogger(__name__)
ALLOWED_FEATURES = {"chatbot", "exam_notes", "quiz", "teach_it_back", "general"}


def save_feedback(session_id: str, feature_type: str, reference_id: str | None, rating: int, comment: str | None) -> dict:
    normalized_session_id = (session_id or "anonymous").strip() or "anonymous"
    normalized_feature = (feature_type or "general").strip().lower()
    if normalized_feature not in ALLOWED_FEATURES:
        normalized_feature = "general"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO feedback (
            user_id_or_session_id, feature_type, reference_id, rating, comment
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            normalized_session_id,
            normalized_feature,
            reference_id,
            1 if int(rating) > 0 else -1,
            comment.strip() if comment else None,
        ),
    )
    conn.commit()
    conn.close()
    return {"ok": True}


def get_feedback_summary() -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT feature_type, COUNT(*) AS total_count,
               SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) AS helpful_count,
               MAX(created_at) AS last_seen
        FROM feedback
        GROUP BY feature_type
        ORDER BY total_count DESC
        """
    ).fetchall()
    conn.close()

    summary = []
    for row in rows:
        total_count = int(row["total_count"] or 0)
        helpful_count = int(row["helpful_count"] or 0)
        helpful_pct = round((helpful_count / total_count) * 100, 1) if total_count else 0.0

        conn = get_db()
        cursor = conn.cursor()
        comments = cursor.execute(
            """
            SELECT comment FROM feedback
            WHERE feature_type = ? AND comment IS NOT NULL AND TRIM(comment) != ''
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (row["feature_type"],),
        ).fetchall()
        conn.close()

        summary.append({
            "feature_type": row["feature_type"],
            "total_count": total_count,
            "helpful_pct": helpful_pct,
            "recent_comments": [c["comment"] for c in comments if c["comment"]],
        })

    return summary
