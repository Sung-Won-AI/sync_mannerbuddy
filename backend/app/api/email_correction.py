# [기능 1] Gmail 실시간 메일 문장 수정
# Chrome 확장(content script)에서 전달받은 문장을 비즈니스 매너 기준으로 교정해 반환한다.

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/email-correction", tags=["email-correction"])


class EmailCorrectionRequest(BaseModel):
    text: str
    target_country: str | None = None  # 상대방 국가 (문화별 매너 기준 적용)


class EmailCorrectionResponse(BaseModel):
    original: str
    corrected: str
    notes: list[str] = []


@router.post("", response_model=EmailCorrectionResponse)
async def correct_email_text(payload: EmailCorrectionRequest) -> EmailCorrectionResponse:
    # TODO: LLM 호출로 비즈니스 매너 교정 수행
    return EmailCorrectionResponse(original=payload.text, corrected=payload.text, notes=[])
