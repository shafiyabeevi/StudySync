"""
Chat API endpoint.
RAG-based chatbot with multilingual support.
"""
from fastapi import APIRouter, HTTPException
from app.services.chatbot import chat_with_document
from app.schemas.models import ChatRequest, ChatResponse, ErrorResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def chat(request: ChatRequest):
    """
    Send a message to the chatbot with document context (RAG).
    Supports multilingual responses — if the student asks in or for a specific
    language, the bot responds in that language.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        result = await chat_with_document(
            document_id=request.document_id,
            user_message=request.message,
            chat_history=[msg.model_dump() for msg in request.chat_history],
        )
        return ChatResponse(
            response=result["response"],
            language=result["language"],
        )
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your question. Please try again."
        )
