from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError
from app.repositories import repository
from app.schemas.feedback import FeedbackRequest, FeedbackResponse


class FeedbackService:
    def save(self, payload: FeedbackRequest) -> FeedbackResponse:
        if payload.analysis_id is not None:
            analysis = repository.get_analysis(
                payload.analysis_id,
                settings.demo_user_id,
            )
            if analysis is None:
                raise ResourceNotFoundError("분석 결과")
        stored = repository.save_feedback(
            {
                "user_id": settings.demo_user_id,
                **payload.model_dump(),
            }
        )
        return FeedbackResponse(feedback_id=stored["id"], saved=True)


feedback_service = FeedbackService()
