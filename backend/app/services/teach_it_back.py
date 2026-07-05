import json
import logging
import os
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.core.local_db import get_db
from app.services.vector_store import retrieve_relevant_chunks_with_ids

logger = logging.getLogger(__name__)

TEACH_IT_BACK_PROMPT = """You are a kind but rigorous teacher helping a student practice explaining ideas in their own words.

The correct source material is below:
{context}

The student is trying to explain this topic: {topic}

Their explanation:
{explanation}

Evaluate their understanding and return valid JSON with these keys:
- rights: a list of the main ideas they explained correctly
- wrongs: a list of inaccurate or misunderstood points
- missing: a list of important ideas they did not mention
- model_answer: a short, ideal explanation of the topic in a teacher-like tone
- score: a number from 0 to 10
- message: a short encouraging note for the student

Be encouraging, never harsh, and keep the feedback constructive.
"""


def _get_gemini_llm():
    settings = get_settings()
    os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.4,
        max_output_tokens=2048,
    )


def _get_groq_llm():
    settings = get_settings()
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0.4,
        max_tokens=2048,
    )


def _normalize_payload(payload: object) -> dict:
    if isinstance(payload, dict):
        return payload
    def _extract_json_from_text(text: str) -> Optional[dict]:
        t = text.strip()
        # Try fenced JSON ```json { ... } ``` or ```{ ... } ```
        import re

        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", t, flags=re.DOTALL)
        if m:
            candidate = m.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # Try to find a top-level JSON object by matching braces
        start = t.find("{")
        if start != -1:
            depth = 0
            for i in range(start, len(t)):
                if t[i] == "{":
                    depth += 1
                elif t[i] == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = t[start:i+1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        # As a last resort, try to parse the whole string
        try:
            return json.loads(t)
        except Exception:
            return None

    if isinstance(payload, str):
        text = payload.strip()
        parsed = _extract_json_from_text(text)
        if isinstance(parsed, dict):
            return parsed

    # If we get here, we couldn't parse structured JSON. Try to coerce sensible defaults
    def _listify(value):
        if not value:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            # split on lines that look like list items
            lines = [l.strip().lstrip("-*") .strip() for l in value.splitlines() if l.strip()]
            if len(lines) > 1:
                return lines
            # fallback: return the single string as one-item list
            return [value.strip()]
        return [str(value)]

    def _parse_score(val):
        if val is None:
            return 5
        if isinstance(val, (int, float)):
            try:
                return max(0, min(10, int(val)))
            except Exception:
                return 5
        # try to extract first integer from strings like '5', '5/10', '5 out of 10'
        import re
        s = str(val)
        m = re.search(r"(\d{1,2})", s)
        if m:
            try:
                n = int(m.group(1))
                return max(0, min(10, n))
            except Exception:
                return 5
        return 5

    return {
        "rights": [],
        "wrongs": [],
        "missing": [],
        "model_answer": str(payload or "A strong explanation should include the key ideas from the source material."),
        "score": 5,
        "message": "You are building understanding step by step — keep going.",
    }


async def evaluate_teach_it_back(document_id: str, topic: str, student_explanation: str) -> dict:
    relevant_chunks = retrieve_relevant_chunks_with_ids(document_id, topic or student_explanation, top_k=5)
    context = "\n\n---\n\n".join([item["text"] for item in relevant_chunks]) if relevant_chunks else "No strongly relevant source chunks were found."

    messages = [
        SystemMessage(content=TEACH_IT_BACK_PROMPT.format(
            context=context,
            topic=topic or "the topic being studied",
            explanation=student_explanation,
        )),
        HumanMessage(content=f"Please assess the student's explanation and return JSON only."),
    ]

    try:
        response = _get_gemini_llm().invoke(messages)
        payload = _normalize_payload(response.content)
        logger.info("Teach-it-back evaluation generated via Gemini")
    except Exception as e:
        logger.warning(f"Gemini teach-it-back failed: {e}, falling back to Groq")
        try:
            response = _get_groq_llm().invoke(messages)
            payload = _normalize_payload(response.content)
            logger.info("Teach-it-back evaluation generated via Groq")
        except Exception as exc:
            logger.error(f"Teach-it-back evaluation failed: {exc}")
            payload = {
                "rights": ["You shared a thoughtful explanation."],
                "wrongs": [],
                "missing": ["A few key ideas from the source material were not mentioned."],
                "model_answer": "A strong answer would explain the main concepts clearly and connect them to the source material.",
                "score": 6,
                "message": "You are on the right track — try one more pass and add the missing detail.",
            }

    def _ensure_list(x):
        if x is None:
            return []
        if isinstance(x, list):
            return x
        if isinstance(x, str):
            lines = [l.strip().lstrip("-*") .strip() for l in x.splitlines() if l.strip()]
            if len(lines) > 1:
                return lines
            return [x.strip()]
        return [str(x)]

    rights = _ensure_list(payload.get("rights"))
    wrongs = _ensure_list(payload.get("wrongs"))
    missing = _ensure_list(payload.get("missing"))
    model_answer = payload.get("model_answer") or "A strong answer would explain the main concepts clearly."

    # Normalize score robustly
    def _parse_score(val):
        if val is None:
            return 5
        if isinstance(val, (int, float)):
            try:
                return max(0, min(10, int(val)))
            except Exception:
                return 5
        import re
        s = str(val)
        m = re.search(r"(\d{1,2})", s)
        if m:
            try:
                n = int(m.group(1))
                return max(0, min(10, n))
            except Exception:
                return 5
        return 5

    score = _parse_score(payload.get("score", 5))
    message = payload.get("message") or "You are making progress — keep refining your explanation."
    # Prefer to inspect the raw model response content for embedded JSON
    raw_text = None
    try:
        raw_text = getattr(response, 'content', None)
    except Exception:
        raw_text = None

    if isinstance(raw_text, str) and '{' in raw_text:
        try:
            start = raw_text.find('{')
            depth = 0
            candidate = None
            for i in range(start, len(raw_text)):
                if raw_text[i] == '{':
                    depth += 1
                elif raw_text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = raw_text[start:i+1]
                        break
            if candidate:
                nested = json.loads(candidate)
                if isinstance(nested, dict):
                    nr = _ensure_list(nested.get('rights'))
                    nw = _ensure_list(nested.get('wrongs'))
                    nm = _ensure_list(nested.get('missing'))
                    if nr:
                        rights = nr
                    if nw:
                        wrongs = nw
                    if nm:
                        missing = nm
                    if nested.get('model_answer'):
                        model_answer = nested.get('model_answer')
                    score = _parse_score(nested.get('score', score))
                    if nested.get('message'):
                        message = nested.get('message')
        except Exception:
            pass
    # If model_answer itself is a fenced code block containing JSON, try to parse it too
    try:
        if isinstance(model_answer, str):
            s = model_answer.strip()
            if s.startswith('```') and '{' in s:
                # extract first {..} in this string
                start = s.find('{')
                depth = 0
                candidate = None
                for i in range(start, len(s)):
                    if s[i] == '{':
                        depth += 1
                    elif s[i] == '}':
                        depth -= 1
                        if depth == 0:
                            candidate = s[start:i+1]
                            break
                if candidate:
                    nested = json.loads(candidate)
                    if isinstance(nested, dict):
                        nr = _ensure_list(nested.get('rights'))
                        nw = _ensure_list(nested.get('wrongs'))
                        nm = _ensure_list(nested.get('missing'))
                        if nr:
                            rights = nr
                        if nw:
                            wrongs = nw
                        if nm:
                            missing = nm
                        if nested.get('model_answer'):
                            model_answer = nested.get('model_answer')
                        score = _parse_score(nested.get('score', score))
                        if nested.get('message'):
                            message = nested.get('message')
    except Exception:
        pass

    settings = get_settings()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO teach_it_back_attempts (
            user_id, document_id, topic, student_explanation, ai_feedback, score
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            settings.DEFAULT_USER_ID,
            document_id,
            topic,
            student_explanation,
            json.dumps({
                "rights": rights,
                "wrongs": wrongs,
                "missing": missing,
                "model_answer": model_answer,
                "score": score,
                "message": message,
            }),
            score,
        ),
    )
    conn.commit()
    attempt_id = cursor.lastrowid
    conn.close()

    return {
        "rights": rights,
        "wrongs": wrongs,
        "missing": missing,
        "model_answer": model_answer,
        "score": score,
        "message": message,
        "attempt_id": attempt_id,
    }


def get_teach_it_back_attempts(document_id: str, topic: Optional[str] = None) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()

    if topic:
        cursor.execute(
            """
            SELECT id, topic, student_explanation, ai_feedback, score, created_at
            FROM teach_it_back_attempts
            WHERE document_id = ? AND topic = ?
            ORDER BY created_at DESC
            """,
            (document_id, topic),
        )
    else:
        cursor.execute(
            """
            SELECT id, topic, student_explanation, ai_feedback, score, created_at
            FROM teach_it_back_attempts
            WHERE document_id = ?
            ORDER BY created_at DESC
            """,
            (document_id,),
        )

    rows = cursor.fetchall()
    conn.close()

    attempts = []
    for row in rows:
        feedback = json.loads(row["ai_feedback"] or "{}") if row["ai_feedback"] else {}
        attempts.append({
            "id": row["id"],
            "topic": row["topic"],
            "student_explanation": row["student_explanation"],
            "feedback": feedback,
            "score": row["score"],
            "created_at": row["created_at"],
        })

    return attempts
