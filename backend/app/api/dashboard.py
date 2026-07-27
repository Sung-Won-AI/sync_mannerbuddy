# [기능 3] 대시보드
# 금주 사용자의 수정 표현 개수, 언어, 비즈니스 매너 온도를 집계해 반환한다.

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


class WeeklySummaryResponse(BaseModel):
    corrected_count: int
    languages: list[str]
    manner_temperature: float  # 0-100


@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary() -> WeeklySummaryResponse:
    # TODO: DB에서 금주 교정 이력 집계
    return WeeklySummaryResponse(corrected_count=0, languages=[], manner_temperature=0)
