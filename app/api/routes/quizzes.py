from fastapi import APIRouter, Query

from app.schemas.quiz import (
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizSetResponse,
)
from app.services.quiz_service import quiz_service

router = APIRouter()


@router.get("", response_model=QuizSetResponse)
async def generate_quizzes(
    limit: int = Query(default=5, ge=1, le=10),
) -> QuizSetResponse:
    return quiz_service.generate(limit)


@router.post(
    "/{question_id}/answer",
    response_model=QuizAnswerResponse,
)
async def answer_quiz(
    question_id: str,
    payload: QuizAnswerRequest,
) -> QuizAnswerResponse:
    return quiz_service.answer(question_id, payload)
