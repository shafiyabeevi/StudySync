from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import AuthenticatedUser, get_current_user
from app.core.documents import get_owned_document
from app.core.supabase_client import get_supabase
from app.schemas.models import TeachItBackRequest, TeachItBackResponse
from app.services.teach_it_back import (
    InsufficientSourceError,
    TeachItBackAIError,
    evaluate_teach_it_back,
    get_teach_it_back_attempts,
)

router = APIRouter()


@router.post("/teach-it-back", response_model=TeachItBackResponse)
async def teach_it_back(
    request: TeachItBackRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    if not request.student_explanation.strip():
        raise HTTPException(status_code=400, detail="Please provide an explanation to evaluate.")

    supabase = get_supabase(user.access_token)
    document = get_owned_document(supabase, user.id, request.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        result = await evaluate_teach_it_back(
            supabase=supabase,
            user_id=user.id,
            document_id=document["id"],
            topic=request.topic,
            student_explanation=request.student_explanation,
        )
    except InsufficientSourceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except TeachItBackAIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return TeachItBackResponse(
        rights=result["rights"],
        wrongs=result["wrongs"],
        missing=result["missing"],
        concept_evaluations=result["concept_evaluations"],
        model_answer=result["model_answer"],
        score=result["score"],
        message=result["message"],
    )


@router.get("/teach-it-back/{document_id}")
async def teach_it_back_attempts(
    document_id: str,
    topic: str | None = None,
    user: AuthenticatedUser = Depends(get_current_user),
):
    supabase = get_supabase(user.access_token)
    document = get_owned_document(supabase, user.id, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "attempts": get_teach_it_back_attempts(
            supabase, user.id, document["id"], topic
        )
    }
