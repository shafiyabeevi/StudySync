from fastapi import APIRouter, HTTPException
from app.schemas.models import TeachItBackRequest, TeachItBackResponse
from app.services.teach_it_back import evaluate_teach_it_back, get_teach_it_back_attempts

router = APIRouter()


@router.post("/teach-it-back", response_model=TeachItBackResponse)
async def teach_it_back(request: TeachItBackRequest):
    if not request.student_explanation.strip():
        raise HTTPException(status_code=400, detail="Please provide an explanation to evaluate.")

    result = await evaluate_teach_it_back(
        document_id=request.document_id,
        topic=request.topic,
        student_explanation=request.student_explanation,
    )

    return TeachItBackResponse(
        rights=result["rights"],
        wrongs=result["wrongs"],
        missing=result["missing"],
        model_answer=result["model_answer"],
        score=result["score"],
        message=result["message"],
    )


@router.get("/teach-it-back/{document_id}")
async def teach_it_back_attempts(document_id: str, topic: str | None = None):
    return {"attempts": get_teach_it_back_attempts(document_id, topic)}
