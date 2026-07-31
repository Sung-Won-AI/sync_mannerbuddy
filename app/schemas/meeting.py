from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.schemas.analysis import AnalysisIssue, AnalysisScores, TargetCountry


class MeetingAnalysisRequest(BaseModel):
    transcript: str = Field(min_length=20)
    target_country: TargetCountry
    language: str = Field(default="en", min_length=2, max_length=10)
    title: str = Field(default="Untitled meeting", max_length=200)
    counterpart_name: str | None = Field(default=None, max_length=200)
    client_request_id: str | None = Field(default=None, max_length=100)

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 20:
            raise ValueError("회의록은 공백 제외 20자 이상이어야 합니다.")
        if len(cleaned) > settings.max_meeting_characters:
            raise ValueError(
                f"회의록은 {settings.max_meeting_characters}자를 넘을 수 없습니다."
            )
        return cleaned


class MeetingFlowPoint(BaseModel):
    segment: int = Field(ge=1)
    temperature: int = Field(ge=0, le=100)
    label: str


class AIMeetingAnalysisResult(BaseModel):
    """AI가 직접 채우는 필드만 모아둔 결과. overall_score/meeting_temperature/flow
    등 서버가 4개 세부 점수로부터 계산해서 붙이는 필드는 여기 없다
    (app/services/meeting_service.py 참고)."""

    scores: AnalysisScores
    issues: list[AnalysisIssue]
    summary: str
    key_points: list[str]
    action_items: list[str]


class MeetingAnalysisResponse(AIMeetingAnalysisResult):
    analysis_id: str
    status: str = "completed"
    title: str
    overall_score: int = Field(ge=0, le=100)
    meeting_temperature: int = Field(ge=0, le=100)
    flow: list[MeetingFlowPoint]
    request_id: str | None = None
    processing_time_ms: int = Field(ge=0)
    created_at: str
