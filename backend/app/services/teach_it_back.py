import json
import logging
import os
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from supabase import Client

from app.core.config import get_settings
from app.services.vector_store import retrieve_relevant_chunks_with_ids

logger = logging.getLogger(__name__)

IMPORTANCE_WEIGHTS = {"high": 3, "medium": 2, "low": 1}
STATUS_COVERAGE = {
    "fully_covered": Decimal("1"),
    "partially_covered": Decimal("0.5"),
    "missed": Decimal("0"),
    "incorrect": Decimal("0"),
}
MAX_SOURCE_CHUNKS = 20

RUBRIC_PROMPT = """You are analyzing excerpts from one student's uploaded study document.

The selected topic is: {topic}

Source excerpts from the selected document:
{context}

First decide whether these excerpts contain enough information specifically about the selected topic to create a meaningful, source-grounded rubric. If not, return source_sufficient=false, an insufficiency_reason, and an empty concepts list.

If sufficient, identify a concise, non-duplicative set of the important concepts that the source itself teaches about this topic. Include only concepts supported by these excerpts. Do not use outside or general textbook knowledge to fill gaps. For each concept include:
- concept: short name
- description: concise meaning based only on the source
- importance: high, medium, or low
- source_evidence: an exact, verbatim excerpt from the provided source text

Return valid JSON only, in this shape:
{{"source_sufficient": true, "insufficiency_reason": "", "concepts": [{{"concept": "...", "description": "...", "importance": "high", "source_evidence": "..."}}]}}
"""

EVALUATION_PROMPT = """You are a kind but rigorous teacher evaluating a student's explanation against a rubric dynamically extracted from their uploaded study document.

Topic: {topic}

PDF-grounded concept rubric (importance weights are supplied for context):
{rubric}

Student explanation:
{explanation}

For every rubric concept, assess the meaning of the student's explanation, not exact wording. Accept semantically equivalent explanations and simpler language. Use only evidence in the student's explanation: quote a short, exact supporting excerpt as student_evidence, or use an empty string if none exists.

Use exactly one status:
- fully_covered: accurate explanation of the core concept
- partially_covered: some accurate understanding, but an important part is absent or unclear
- missed: not addressed
- incorrect: addressed with a materially wrong explanation

Do not give credit for unrelated facts or general textbook knowledge. Encouragement must not influence the status. Do not calculate a score.

Return valid JSON only, with one evaluation for every rubric concept:
{{"concept_evaluations": [{{"concept": "...", "status": "fully_covered", "student_evidence": "...", "feedback": "..."}}], "model_answer": "A concise, source-grounded ideal explanation.", "message": "A short, encouraging and constructive note."}}
"""


class InsufficientSourceError(ValueError):
    """Raised when the selected document has too little topic-specific evidence."""


class TeachItBackAIError(RuntimeError):
    """Raised when the rubric or evaluation cannot be generated reliably."""


def _get_gemini_llm():
    settings = get_settings()
    os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.2,
        max_output_tokens=4096,
    )


def _get_groq_llm():
    settings = get_settings()
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0.2,
        max_tokens=4096,
    )


def _parse_json_response(content: object) -> dict:
    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        raise TeachItBackAIError("The AI returned a non-text response.")

    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            raise TeachItBackAIError("The AI response did not contain valid JSON.")
        text = text[start:end + 1]

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TeachItBackAIError("The AI response did not contain valid JSON.") from exc
    if not isinstance(parsed, dict):
        raise TeachItBackAIError("The AI response must be a JSON object.")
    return parsed


def _invoke_json(messages: list) -> dict:
    try:
        response = _get_gemini_llm().invoke(messages)
        return _parse_json_response(response.content)
    except Exception as gemini_error:
        logger.warning("Gemini Teach It Back request failed; trying Groq: %s", gemini_error)
        try:
            response = _get_groq_llm().invoke(messages)
            return _parse_json_response(response.content)
        except Exception as groq_error:
            logger.error("Teach It Back AI providers failed: %s", groq_error)
            raise TeachItBackAIError(
                "The evaluation service is temporarily unavailable. Please try again."
            ) from groq_error


def invoke_ai_json(messages: list) -> dict:
    """Run a JSON-returning request through the configured Gemini/Groq providers."""
    return _invoke_json(messages)


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _generate_rubric(topic: str, context: str) -> list[dict]:
    result = _invoke_json([
        SystemMessage(content=RUBRIC_PROMPT.format(topic=topic, context=context)),
        HumanMessage(content="Analyze the supplied excerpts and return the requested JSON."),
    ])
    concepts = result.get("concepts")
    if result.get("source_sufficient") is not True:
        reason = result.get("insufficiency_reason") or (
            "The selected document does not provide enough information about this topic."
        )
        raise InsufficientSourceError(str(reason))
    if not isinstance(concepts, list) or not concepts:
        raise InsufficientSourceError(
            "The selected document does not provide enough information about this topic."
        )

    normalized_context = _normalized_text(context)
    rubric = []
    seen = set()
    for item in concepts:
        if not isinstance(item, dict):
            continue
        name = str(item.get("concept", "")).strip()
        description = str(item.get("description", "")).strip()
        importance = str(item.get("importance", "")).strip().lower()
        evidence = str(item.get("source_evidence", "")).strip()
        normalized_name = _normalized_text(name)
        if (
            not name
            or not description
            or importance not in IMPORTANCE_WEIGHTS
            or not evidence
            or normalized_name in seen
            or _normalized_text(evidence) not in normalized_context
        ):
            continue
        seen.add(normalized_name)
        rubric.append({
            "concept": name,
            "description": description,
            "importance": importance,
            "source_evidence": evidence,
            "weight": IMPORTANCE_WEIGHTS[importance],
        })

    if not rubric:
        raise TeachItBackAIError(
            "A source-grounded rubric could not be validated for this topic."
        )
    return rubric


def _evaluate_rubric(topic: str, rubric: list[dict], explanation: str) -> dict:
    result = _invoke_json([
        SystemMessage(content=EVALUATION_PROMPT.format(
            topic=topic,
            rubric=json.dumps(rubric, ensure_ascii=False),
            explanation=explanation,
        )),
        HumanMessage(content="Evaluate every concept and return the requested JSON."),
    ])
    raw_evaluations = result.get("concept_evaluations")
    if not isinstance(raw_evaluations, list):
        raise TeachItBackAIError("The AI did not evaluate the rubric concepts.")

    evaluations_by_name = {}
    for item in raw_evaluations:
        if isinstance(item, dict) and isinstance(item.get("concept"), str):
            evaluations_by_name[_normalized_text(item["concept"])] = item

    normalized_explanation = _normalized_text(explanation)
    evaluations = []
    for concept in rubric:
        item = evaluations_by_name.get(_normalized_text(concept["concept"]))
        if item is None:
            raise TeachItBackAIError("The AI omitted one or more rubric concepts.")
        status = item.get("status")
        if status not in STATUS_COVERAGE:
            raise TeachItBackAIError("The AI returned an invalid concept status.")
        student_evidence = str(item.get("student_evidence") or "").strip()
        if (
            status != "missed"
            and (
                not student_evidence
                or _normalized_text(student_evidence) not in normalized_explanation
            )
        ):
            status = "missed"
            student_evidence = ""
        if status == "missed":
            student_evidence = ""
        feedback = str(item.get("feedback") or "").strip()
        evaluations.append({
            **concept,
            "status": status,
            "student_evidence": student_evidence,
            "feedback": feedback,
            "points_earned": float(Decimal(concept["weight"]) * STATUS_COVERAGE[status]),
        })

    total_weight = sum(concept["weight"] for concept in evaluations)
    earned_weight = sum(
        Decimal(str(concept["points_earned"])) for concept in evaluations
    )
    score = int(
        (earned_weight * 10 / total_weight).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    model_answer = result.get("model_answer")
    message = result.get("message")
    if not isinstance(model_answer, str) or not model_answer.strip():
        raise TeachItBackAIError("The AI did not return a model answer.")
    if not isinstance(message, str) or not message.strip():
        message = "You are making progress—keep refining your explanation."

    rights = [
        item["concept"] + ": " + item["feedback"]
        for item in evaluations
        if item["status"] in ("fully_covered", "partially_covered")
    ]
    wrongs = [
        item["concept"] + ": " + item["feedback"]
        for item in evaluations
        if item["status"] == "incorrect"
    ]
    missing = [
        item["concept"] + ": " + item["description"]
        for item in evaluations
        if item["status"] == "missed"
    ]
    return {
        "concept_evaluations": evaluations,
        "rights": rights,
        "wrongs": wrongs,
        "missing": missing,
        "model_answer": model_answer.strip(),
        "score": score,
        "message": message.strip(),
    }


async def evaluate_teach_it_back(
    supabase: Client,
    user_id: str,
    document_id: str,
    topic: str,
    student_explanation: str,
    extracted_text: str | None = None,
) -> dict:
    search_query = topic.strip() or student_explanation
    relevant_chunks = retrieve_relevant_chunks_with_ids(
        document_id,
        search_query,
        top_k=MAX_SOURCE_CHUNKS,
        extracted_text=extracted_text,
    )
    context = "\n\n---\n\n".join(
        item["text"].strip()
        for item in relevant_chunks
        if isinstance(item.get("text"), str) and item["text"].strip()
    )
    if not context:
        raise InsufficientSourceError(
            "There is not enough searchable source material in this document to evaluate this topic."
        )

    rubric = _generate_rubric(topic or "the selected topic", context)
    result = _evaluate_rubric(topic or "the selected topic", rubric, student_explanation)

    feedback = {
        key: result[key]
        for key in (
            "concept_evaluations",
            "rights",
            "wrongs",
            "missing",
            "model_answer",
            "score",
            "message",
        )
    }
    attempt = supabase.table("teach_it_back_attempts").insert({
        "user_id": user_id,
        "document_id": document_id,
        "topic": topic,
        "student_explanation": student_explanation,
        "ai_feedback": feedback,
        "score": result["score"],
    }).execute().data
    result["attempt_id"] = attempt[0]["id"] if attempt else None
    return result


def get_teach_it_back_attempts(
    supabase: Client,
    user_id: str,
    document_id: str,
    topic: Optional[str] = None,
) -> list[dict]:
    query = (
        supabase.table("teach_it_back_attempts")
        .select("id,topic,student_explanation,ai_feedback,score,created_at")
        .eq("user_id", user_id)
        .eq("document_id", document_id)
    )
    if topic:
        query = query.eq("topic", topic)

    rows = query.order("created_at", desc=True).execute().data
    attempts = []
    for row in rows:
        feedback = row.get("ai_feedback") or {}
        if isinstance(feedback, str):
            feedback = json.loads(feedback)
        attempts.append({
            "id": row["id"],
            "topic": row["topic"],
            "student_explanation": row["student_explanation"],
            "feedback": feedback,
            "score": row["score"],
            "created_at": row["created_at"],
        })
    return attempts
