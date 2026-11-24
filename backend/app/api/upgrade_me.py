import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import AuthenticatedUser, get_current_user
from app.core.documents import get_owned_document
from app.core.supabase_client import get_supabase
from app.schemas.models import (
    UpgradeMeFlowchartRequest,
    UpgradeMeFlowchartResponse,
    UpgradeMeQuizRequest,
    UpgradeMeQuizResponse,
    UpgradeMeQuizEvaluateRequest,
    UpgradeMeQuizEvaluateResponse,
)
from app.services.upgrade_me import (
    UpgradeMeAIError,
    UpgradeMeSourceError,
    evaluate_upgrade_me_quiz,
    generate_upgrade_me_flowchart,
    generate_upgrade_me_quiz,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_document(request, user: AuthenticatedUser):
    supabase = get_supabase(user.access_token)
    document = get_owned_document(supabase, user.id, request.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    if str(document.get("file_type") or "").lower() != "pdf":
        raise HTTPException(status_code=400, detail="Upgrade Me accepts PDF documents only.")
    if document.get("status") != "ready":
        raise HTTPException(status_code=409, detail="The selected document is still being processed.")
    if not str(document.get("extracted_text") or "").strip():
        raise HTTPException(status_code=422, detail="The selected document has no usable text.")
    return document


def _raise_service_error(exc: Exception, user_id: str):
    if isinstance(exc, UpgradeMeSourceError):
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if isinstance(exc, UpgradeMeAIError):
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    logger.error("Unexpected Upgrade Me failure for user %s: %s", user_id, exc, exc_info=True)
    raise HTTPException(status_code=500, detail="Upgrade Me could not complete the request.") from exc


@router.get("/upgrade-me")
async def upgrade_me_topics(
    user: AuthenticatedUser = Depends(get_current_user),
):
    return {"topics": [], "improved": []}


@router.post("/upgrade-me/flowchart", response_model=UpgradeMeFlowchartResponse)
async def upgrade_me_flowchart(
    request: UpgradeMeFlowchartRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    document = _get_document(request, user)
    try:
        return generate_upgrade_me_flowchart(document, request.topic)
    except (UpgradeMeSourceError, UpgradeMeAIError) as exc:
        _raise_service_error(exc, user.id)
    except Exception as exc:
        _raise_service_error(exc, user.id)


@router.post("/upgrade-me/quiz", response_model=UpgradeMeQuizResponse)
async def upgrade_me_quiz(
    request: UpgradeMeQuizRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    document = _get_document(request, user)
    try:
        return generate_upgrade_me_quiz(document, request.topic)
    except (UpgradeMeSourceError, UpgradeMeAIError) as exc:
        _raise_service_error(exc, user.id)
    except Exception as exc:
        _raise_service_error(exc, user.id)


@router.post("/upgrade-me/quiz/evaluate", response_model=UpgradeMeQuizEvaluateResponse)
async def upgrade_me_quiz_evaluate(
    request: UpgradeMeQuizEvaluateRequest,
    user: AuthenticatedUser = Depends(get_current_user),
):
    document = _get_document(request, user)
    try:
        return evaluate_upgrade_me_quiz(document, request.topic, request.answers)
    except (UpgradeMeSourceError, UpgradeMeAIError) as exc:
        _raise_service_error(exc, user.id)
    except Exception as exc:
        _raise_service_error(exc, user.id)
