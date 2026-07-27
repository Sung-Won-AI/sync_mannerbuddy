# [기능 4] 복습 & 3분 퀴즈
# 금주에 수정한 표현 목록을 다시 복습하고, 해당 표현들로 구성된 3분 분량의 퀴즈를 제공한다.

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/review", tags=["review"])


class CorrectedExpression(BaseModel):
    id: str
    original: str
    corrected: str


class QuizQuestion(BaseModel):
    id: str
    prompt: str
    choices: list[str]
    answer_index: int


@router.get("/weekly-expressions", response_model=list[CorrectedExpression])
async def get_weekly_expressions() -> list[CorrectedExpression]:
    # TODO: DB에서 금주 교정 표현 목록 조회
    return []


@router.get("/quiz", response_model=list[QuizQuestion])
async def get_weekly_quiz() -> list[QuizQuestion]:
    # TODO: 금주 교정 표현 기반 퀴즈 생성 (3분 분량)
    return []
