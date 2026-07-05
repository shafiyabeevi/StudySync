"""
Exam notes generation service.
Uses Gemini to extract important study points from document text.
"""
import os
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

EXAM_NOTES_SYSTEM_PROMPT = """You are an expert exam-preparation tutor. Your task is to read the provided study material and extract the most important points a student MUST revise before an exam.

You MUST respond with valid JSON in this exact format:
{
  "title": "Chapter/Topic Title",
  "sub_topics": [
    {
      "heading": "Sub-topic Name",
      "points": [
        "Key point 1 — clear and concise",
        "Key point 2 — include any formula or definition",
        "Key point 3"
      ]
    }
  ],
  "key_definitions": [
    {"term": "Term Name", "definition": "Clear definition"},
  ],
  "important_formulas": [
    "Formula 1: description"
  ],
  "likely_exam_questions": [
    "Question that is likely to appear in exams?"
  ]
}

Rules:
- Extract ONLY the most important, exam-relevant information
- Group points logically by sub-topic
- Include definitions, formulas, key terms, and likely exam questions
- Be concise but complete — students will use this as their revision sheet
- If there are no formulas or definitions, return empty arrays for those fields
- Respond ONLY with the JSON, no markdown code fences, no extra text"""


def _get_gemini_llm():
    settings = get_settings()
    os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
        max_output_tokens=8192,
    )


def _get_groq_llm():
    settings = get_settings()
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0.3,
        max_tokens=8192,
    )


async def generate_exam_notes(text: str, filename: str) -> dict:
    """
    Generate structured exam notes from document text.
    Uses Gemini as primary, falls back to Groq on failure.
    Returns a dict with the structured notes.
    """
    # Truncate very long documents to fit context window
    max_chars = 100000  # ~25k tokens, well within Gemini's context
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Document truncated for processing...]"

    messages = [
        SystemMessage(content=EXAM_NOTES_SYSTEM_PROMPT),
        HumanMessage(content=f"Here is the study material from '{filename}':\n\n{text}")
    ]

    # Try Gemini first
    try:
        llm = _get_gemini_llm()
        response = llm.invoke(messages)
        notes = _parse_notes_response(response.content)
        logger.info(f"Generated exam notes for '{filename}' using Gemini")
        return notes
    except Exception as e:
        logger.warning(f"Gemini failed for notes generation: {e}, falling back to Groq")

    # Fallback to Groq
    try:
        llm = _get_groq_llm()
        response = llm.invoke(messages)
        notes = _parse_notes_response(response.content)
        logger.info(f"Generated exam notes for '{filename}' using Groq (fallback)")
        return notes
    except Exception as e:
        logger.error(f"Both LLMs failed for notes generation: {e}")
        return _build_fallback_notes(text, filename)


def _parse_notes_response(content: str) -> dict:
    """Parse the LLM response into a structured dict."""
    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # If JSON parsing fails, return as unstructured text
        logger.warning("Failed to parse notes as JSON, returning as text")
        return {
            "title": "Study Notes",
            "sub_topics": [{"heading": "Notes", "points": content.split("\n")}],
            "key_definitions": [],
            "important_formulas": [],
            "likely_exam_questions": [],
        }


def _build_fallback_notes(text: str, filename: str) -> dict:
    """Create simple, structured notes locally when LLM services are unavailable."""
    title = filename.rsplit(".", 1)[0] if "." in filename else filename
    cleaned_text = re.sub(r"\s+", " ", text or "").strip()

    sections = []
    for chunk in re.split(r"(?=(?:^|\n)(?:\d+\.|[A-Z][A-Za-z]+))", text or ""):
        if chunk and len(chunk.strip()) > 40:
            sections.append(chunk.strip())
    if not sections:
        sections = [cleaned_text[:1200]] if cleaned_text else ["Document content is available for review."]

    sub_topics = []
    for index, section in enumerate(sections[:4], start=1):
        sub_topics.append({
            "heading": f"Key point {index}",
            "points": [
                re.sub(r"\s+", " ", section)[:280],
                "Review the document carefully and note the main ideas, definitions, and examples.",
            ],
        })

    definitions = []
    for match in re.finditer(r"([A-Z][A-Za-z0-9 ]+?)\s*[:\-]\s*(.+)", text or ""):
        term = match.group(1).strip()
        definition = match.group(2).strip()
        if term and definition and len(definitions) < 4:
            definitions.append({"term": term, "definition": definition[:220]})

    formulas = []
    for match in re.finditer(r"([A-Za-z0-9_]+\s*[=<>+\-/*]\s*[A-Za-z0-9_().\s]+)", text or ""):
        formulas.append(match.group(1).strip())
        if len(formulas) >= 3:
            break

    return {
        "title": title,
        "sub_topics": sub_topics,
        "key_definitions": definitions,
        "important_formulas": formulas,
        "likely_exam_questions": [
            "What are the main ideas covered in this document?",
            "Which definitions or terms are most important to remember?",
            "What examples or procedures should be reviewed carefully?",
        ],
    }
