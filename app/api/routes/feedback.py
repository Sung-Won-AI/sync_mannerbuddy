from fastapi import APIRouter, status

from app.schemas.feedback import FeedbackRequest, FeedbackResponse
from app.services.feedback_service import feedback_service

router = APIRouter()


@router.post(
    "",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def save_feedback(payload: FeedbackRequest) -> FeedbackResponse:
    return feedback_service.save(payload)
