from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings


class TargetCountry(str, Enum):
    US = "US"
    JP = "JP"
    CN = "CN"


class AnalysisCategory(str, Enum):
    VOCABULARY = "vocabulary"
    TONE = "tone"
    TABOO = "taboo"
    MANNERS = "manners"


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EmailAnalysisRequest(BaseModel):
    text: str = Field(min_length=10)
    target_country: TargetCountry
    language: str = Field(default="en", min_length=2, max_length=10)
    source: str = Field(default="gmail", max_length=30)
    mode: str = Field(default="manual", pattern="^(manual|automatic)$")
    client_request_id: str | None = Field(default=None, max_length=100)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("이메일 본문은 공백 제외 10자 이상이어야 합니다.")
        if len(cleaned) > settings.max_email_characters:
            raise ValueError(
                f"이메일 본문은 {settings.max_email_characters}자를 넘을 수 없습니다."
            )
        return cleaned


class AnalysisScores(BaseModel):
    vocabulary: int = Field(ge=0, le=100)
    tone: int = Field(ge=0, le=100)
    taboo: int = Field(ge=0, le=100)
    manners: int = Field(ge=0, le=100)


class IssueFixType(str, Enum):
    REPLACE = "replace"  # suggestion이 original 자리에 그대로 넣을 수 있는 실제 대체 문장
    INSERT = "insert"  # suggestion이 "이런 걸 추가하라"는 권고일 뿐, 넣을 문장은 사용자가 직접 작성


class AnalysisIssue(BaseModel):
    issue_id: str
    original: str
    start_index: int = Field(ge=0)
    end_index: int = Field(ge=0)
    category: AnalysisCategory
    severity: IssueSeverity
    reason: str
    suggestion: str
    fix_type: IssueFixType = IssueFixType.REPLACE


class AIAnalysisResult(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    scores: AnalysisScores
    issues: list[AnalysisIssue]
    revised_text: str
    summary: str


class EmailAnalysisResponse(AIAnalysisResult):
    analysis_id: str
    status: str = "completed"
    request_id: str | None = None
    processing_time_ms: int = Field(ge=0)
    created_at: datetime

