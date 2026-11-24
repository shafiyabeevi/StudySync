"""
RAG-based chatbot service with multilingual support.
Retrieves relevant document context and answers student questions,
responding in whichever language the student requests.
"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.core.config import get_settings
from app.services.vector_store import retrieve_relevant_chunks
import logging

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """You are a helpful, patient study assistant chatbot. You help students understand their study material and prepare for exams.

CONTEXT FROM THE STUDENT'S DOCUMENT:
{context}

RULES:
1. Answer questions using the document context provided above. If the answer isn't in the context, say so honestly but try to help with your general knowledge.
2. Be concise but thorough — students want clear explanations, not essays.
3. LANGUAGE HANDLING (CRITICAL):
   - If the student asks a question in English, answer in English.
   - If the student asks for an explanation in a specific language (e.g., "explain in Tamil", "தமிழில் விளக்கவும்", "हिंदी में समझाओ"), you MUST respond in that exact language.
   - Detect the requested language from the student's message itself.
   - When answering in another language, answer ONLY the specific question or concept asked about — do NOT re-summarize the entire document.
4. Use examples, analogies, or simplified explanations when the concept is complex.
5. If the student asks about a formula, show the formula clearly and explain each variable.
6. Format your response with markdown for readability (bullet points, bold, headings) where appropriate."""


def _build_messages(
    context: str,
    user_message: str,
    chat_history: list[dict],
) -> list:
    """Build the message list for the LLM call."""
    messages = [
        SystemMessage(content=CHAT_SYSTEM_PROMPT.format(context=context))
    ]

    # Add chat history
    for msg in chat_history[-10:]:  # Keep last 10 messages for context window management
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # Add current user message
    messages.append(HumanMessage(content=user_message))
    return messages


def _get_gemini_llm():
    settings = get_settings()
    os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.5,
        max_output_tokens=4096,
    )


def _get_groq_llm():
    settings = get_settings()
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.GROQ_API_KEY,
        temperature=0.5,
        max_tokens=4096,
    )


async def chat_with_document(
    document_id: str,
    user_message: str,
    chat_history: list[dict],
) -> dict:
    """
    Process a chat message with RAG context from the document.
    Returns dict with 'response' and 'language'.
    """
    # Retrieve relevant chunks from the document
    relevant_chunks = retrieve_relevant_chunks(document_id, user_message, top_k=5)

    if relevant_chunks:
        context = "\n\n---\n\n".join(relevant_chunks)
    else:
        context = "(No specific context found in the document for this question. Answer based on general knowledge.)"

    messages = _build_messages(context, user_message, chat_history)

    # Try Gemini first
    try:
        llm = _get_gemini_llm()
        response = llm.invoke(messages)
        detected_lang = _detect_response_language(user_message)
        logger.info(f"Chat response generated via Gemini (lang: {detected_lang})")
        return {"response": response.content, "language": detected_lang}
    except Exception as e:
        logger.warning(f"Gemini chat failed: {e}, falling back to Groq")

    # Fallback to Groq
    try:
        llm = _get_groq_llm()
        response = llm.invoke(messages)
        detected_lang = _detect_response_language(user_message)
        logger.info(f"Chat response generated via Groq fallback (lang: {detected_lang})")
        return {"response": response.content, "language": detected_lang}
    except Exception as e:
        logger.error(f"Both LLMs failed for chat: {e}")
        raise ValueError("AI service is temporarily unavailable. Please try again in a moment.")


def _detect_response_language(user_message: str) -> str:
    """
    Simple heuristic to detect which language the student requested.
    The actual language switching is handled by the LLM via the system prompt.
    This is just for metadata/logging purposes.
    """
    lower = user_message.lower()
    language_hints = {
        "tamil": "ta", "தமிழ்": "ta", "தமிழில்": "ta",
        "hindi": "hi", "हिंदी": "hi", "हिन्दी": "hi",
        "telugu": "te", "తెలుగు": "te",
        "kannada": "kn", "ಕನ್ನಡ": "kn",
        "malayalam": "ml", "മലയാളം": "ml",
        "bengali": "bn", "বাংলা": "bn",
        "marathi": "mr", "मराठी": "mr",
        "gujarati": "gu", "ગુજરાતી": "gu",
        "french": "fr", "français": "fr",
        "spanish": "es", "español": "es",
        "german": "de", "deutsch": "de",
        "chinese": "zh", "中文": "zh",
        "japanese": "ja", "日本語": "ja",
        "korean": "ko", "한국어": "ko",
        "arabic": "ar", "العربية": "ar",
    }
    for hint, code in language_hints.items():
        if hint in lower:
            return code
    return "en"
