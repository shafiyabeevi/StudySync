import hashlib
import json
import re
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.teach_it_back import invoke_ai_json
from app.services.vector_store import retrieve_relevant_chunks_with_ids


class UpgradeMeSourceError(ValueError):
    pass


class UpgradeMeAIError(RuntimeError):
    pass


def make_concept_id(document_id: str, topic: str, concept: str) -> str:
    identity = "\x1f".join((document_id, " ".join(topic.casefold().split()), " ".join(concept.casefold().split())))
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _is_after(value: Optional[str], reference: Optional[str]) -> bool:
    return bool(value and (not reference or value > reference))


def _current_progress_status(
    evaluation_status: str,
    attempt_created_at: Optional[str],
    progress: Optional[dict],
) -> str:
    if evaluation_status == "fully_covered":
        return "improved"
    if progress:
        last_evaluation = progress.get("last_evaluation_status")
        if _is_after(progress.get("last_evaluated_at"), attempt_created_at):
            return "improved" if last_evaluation == "fully_covered" else "practicing"
        if progress.get("improvement_status") == "practicing" and _is_after(
            progress.get("last_practiced_at"), attempt_created_at
        ):
            return "practicing"
    return "needs_improvement"


def _source_context(document: dict, topic: str) -> str:
    chunks = retrieve_relevant_chunks_with_ids(
        str(document["id"]),
        topic.strip(),
        top_k=15,
        extracted_text=document.get("extracted_text"),
    )
    context = "\n\n---\n\n".join(
        str(item.get("text") or "").strip()
        for item in chunks
        if isinstance(item, dict) and str(item.get("text") or "").strip()
    )
    if not context:
        raise UpgradeMeSourceError(
            "The selected PDF does not contain enough retrievable content for this topic."
        )
    return context[:18000]


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _invoke(payload_messages: list) -> dict:
    try:
        return invoke_ai_json(payload_messages)
    except Exception as exc:
        if isinstance(exc, UpgradeMeAIError):
            raise
        raise UpgradeMeAIError("The AI generation service is temporarily unavailable. Please try again.") from exc


FLOWCHART_PROMPT = """Create a beginner-friendly flowchart for the selected topic using only this uploaded document.

Topic: {topic}
Document text:
{context}

Return JSON only:
{{"title":"...","summary":"...","nodes":[{{"id":"n1","kind":"start","label":"...","explanation":"..."}}],"edges":[{{"from":"n1","to":"n2","label":"..."}}]}}

Rules:
- Use 5 to 10 nodes.
- Include short, beginner-readable explanations.
- Use start, step, decision, concept, and end kinds where appropriate.
- Decisions may branch with edge labels such as Yes/No or Next.
- Every label and explanation must be supported by the document text.
- Do not add unrelated textbook facts or outside examples.
- If the document does not cover the topic, set source_sufficient false, but keep the JSON shape."""


def generate_upgrade_me_flowchart(document: dict, topic: str) -> dict:
    topic = topic.strip()
    if not topic:
        raise UpgradeMeSourceError("Enter a topic to improve.")
    context = _source_context(document, topic)
    result = _invoke([
        SystemMessage(content=FLOWCHART_PROMPT.format(topic=topic, context=context)),
        HumanMessage(content="Generate the source-grounded beginner flowchart."),
    ])

    nodes = result.get("nodes")
    edges = result.get("edges")
    if not isinstance(nodes, list) or len(nodes) < 3 or not isinstance(edges, list):
        raise UpgradeMeAIError("The AI could not create a usable flowchart. Please try again.")

    normalized_context = _normalize(context)
    valid_nodes = []
    seen = set()
    for item in nodes:
        if not isinstance(item, dict):
            continue
        node_id = str(item.get("id", "")).strip()
        label = str(item.get("label", "")).strip()
        explanation = str(item.get("explanation", "")).strip()
        kind = str(item.get("kind", "concept")).strip()
        if not node_id or node_id in seen or not label or not explanation or kind not in {"start", "concept", "decision", "step", "end"}:
            continue
        seen.add(node_id)
        valid_nodes.append({"id": node_id, "kind": kind, "label": label, "explanation": explanation})
    if len(valid_nodes) < 3:
        raise UpgradeMeAIError("The generated flowchart could not be validated. Please try again.")

    valid_ids = {item["id"] for item in valid_nodes}
    valid_edges = []
    for item in edges:
        if not isinstance(item, dict):
            continue
        from_id = str(item.get("from", "")).strip()
        to_id = str(item.get("to", "")).strip()
        if from_id in valid_ids and to_id in valid_ids:
            valid_edges.append({"from": from_id, "to": to_id, "label": str(item.get("label", "")).strip()})
    if not valid_edges:
        raise UpgradeMeAIError("The generated flowchart has no valid connections.")

    title = str(result.get("title", topic)).strip() or topic
    summary = str(result.get("summary", "")).strip()
    if not summary:
        summary = f"A document-grounded overview of {topic}."
    return {"title": title, "summary": summary, "nodes": valid_nodes, "edges": valid_edges}


QUIZ_PROMPT = """Create a document-grounded quiz for the topic below.

Topic: {topic}
Document text:
{context}

Return JSON only:
{{"questions":[{{"id":"q1","type":"multiple_choice","question":"...","options":["...","...","...","..."],"correct_answer":"...","explanation":"..."}}]}}

Create 5 questions: 3 multiple_choice and 2 concept. Concepts must require short explanations.
All questions, answers, options, and explanations must be supported by the document.
Do not ask unsupported or unrelated trivia.
Multiple-choice correct_answer must exactly match one options entry."""


def generate_upgrade_me_quiz(document: dict, topic: str) -> dict:
    topic = topic.strip()
    if not topic:
        raise UpgradeMeSourceError("Enter a topic to improve.")
    context = _source_context(document, topic)
    result = _invoke([
        SystemMessage(content=QUIZ_PROMPT.format(topic=topic, context=context)),
        HumanMessage(content="Generate the document-grounded quiz."),
    ])
    raw = result.get("questions")
    if not isinstance(raw, list) or len(raw) < 3:
        raise UpgradeMeAIError("The AI could not generate a usable quiz. Please try again.")

    questions = []
    seen = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        question_type = item.get("type")
        question = str(item.get("question", "")).strip()
        correct = str(item.get("correct_answer", "")).strip()
        explanation = str(item.get("explanation", "")).strip()
        options = item.get("options") if isinstance(item.get("options"), list) else []
        options = [str(option).strip() for option in options if str(option).strip()]
        if question_type not in {"multiple_choice", "concept"} or not question or not correct or not explanation:
            continue
        if question_type == "multiple_choice" and (len(options) < 2 or correct not in options):
            continue
        key = _normalize(question)
        if key in seen:
            continue
        seen.add(key)
        questions.append({
            "id": str(item.get("id", f"q{index + 1}")),
            "type": question_type,
            "question": question,
            "options": options if question_type == "multiple_choice" else [],
            "correct_answer": correct,
            "explanation": explanation,
        })
    if len(questions) < 3:
        raise UpgradeMeAIError("The generated quiz could not be validated. Please try again.")
    return {"topic": topic, "questions": questions[:5]}


EVALUATION_PROMPT = """Evaluate the student's quiz answers against the selected uploaded document.

Topic: {topic}
Document text:
{context}
Quiz answers:
{answers}

Return JSON only:
{{"results":[{{"question_id":"q1","correct":true,"feedback":"..."}}],"feedback":"A short final feedback sentence."}}

For multiple-choice, the provided answer is correct only when it exactly matches correct_answer.
For concept questions, accept semantically equivalent explanations and mark correct when the answer accurately covers the concept from the document.
Do not mark unrelated but plausible outside knowledge as correct."""


def evaluate_upgrade_me_quiz(document: dict, topic: str, answers: list) -> dict:
    context = _source_context(document, topic)
    prepared = [
        {
            "question_id": getattr(answer, "question_id", ""),
            "question": getattr(answer, "question", ""),
            "type": getattr(answer, "type", "concept"),
            "student_answer": getattr(answer, "answer", ""),
            "correct_answer": getattr(answer, "correct_answer", ""),
            "explanation": getattr(answer, "explanation", ""),
        }
        for answer in answers
    ]
    result = _invoke([
        SystemMessage(content=EVALUATION_PROMPT.format(
            topic=topic,
            context=context,
            answers=json.dumps(prepared, ensure_ascii=False),
        )),
        HumanMessage(content="Evaluate all answers and return the JSON result."),
    ])
    raw_results = result.get("results")
    if not isinstance(raw_results, list):
        raise UpgradeMeAIError("The AI could not evaluate the quiz. Please try again.")

    answers_by_id = {item["question_id"]: item for item in prepared}
    results = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        question_id = str(item.get("question_id", ""))
        answer = answers_by_id.get(question_id)
        if not answer:
            continue
        correct = bool(item.get("correct"))
        if answer["type"] == "multiple_choice":
            correct = _normalize(answer["student_answer"]) == _normalize(answer["correct_answer"])
        results.append({
            "question_id": question_id,
            "correct": correct,
            "correct_answer": answer["correct_answer"],
            "explanation": answer["explanation"],
            "feedback": str(item.get("feedback", "")).strip(),
        })

    total = len(prepared)
    score = sum(1 for item in results if item["correct"])
    feedback = str(result.get("feedback", "")).strip()
    if not feedback:
        feedback = f"You scored {score} out of {total}."
    return {"score": score, "total": total, "feedback": feedback, "results": results}
