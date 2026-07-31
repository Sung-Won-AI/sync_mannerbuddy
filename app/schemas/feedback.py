from enum import Enum

from pydantic import BaseModel, Field


class SuggestionAction(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COPIED = "copied"
    DISMISSED = "dismissed"


class AnalysisActionRequest(BaseModel):
    issue_id: str
    action: SuggestionAction


class AnalysisActionResponse(BaseModel):
    saved: bool
    analysis_id: str
    issue_id: str
    action: SuggestionAction


class FeedbackRequest(BaseModel):
    analysis_id: str | None = None
    rating: int = Field(ge=1, le=5)
    is_helpful: bool
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    feedback_id: str
    saved: bool
