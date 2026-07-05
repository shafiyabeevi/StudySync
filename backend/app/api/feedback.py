from fastapi import APIRouter
from app.schemas.models import FeedbackRequest
from app.services.feedback import get_feedback_summary, save_feedback

router = APIRouter()


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    save_feedback(
        session_id=request.session_id,
        feature_type=request.feature_type,
        reference_id=request.reference_id,
        rating=request.rating,
        comment=request.comment,
    )
    return {"ok": True}


@router.get("/feedback/summary")
async def feedback_summary():
    return {"summary": get_feedback_summary()}
