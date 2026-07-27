# [기능 2] 화상 회의 요약 및 표현 수정
# 회의 완료 후 전달된 회의록(전사 텍스트)을 요약하고, 회의 중 사용된 표현의 매너 교정을 함께 제공한다.

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/meeting-summary", tags=["meeting-summary"])


class MeetingSummaryRequest(BaseModel):
    transcript: str
    participants: list[str] = []


class ExpressionCorrection(BaseModel):
    original: str
    corrected: str


class MeetingSummaryResponse(BaseModel):
    summary: str
    corrections: list[ExpressionCorrection] = []


@router.post("", response_model=MeetingSummaryResponse)
async def summarize_meeting(payload: MeetingSummaryRequest) -> MeetingSummaryResponse:
    # TODO: LLM 호출로 회의 요약 및 표현 교정 수행
    return MeetingSummaryResponse(summary="", corrections=[])
