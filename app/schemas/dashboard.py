from pydantic import BaseModel, Field

from app.schemas.analysis import AnalysisScores


class CountryUsage(BaseModel):
    country: str
    count: int = Field(ge=0)


class FrequentIssue(BaseModel):
    category: str
    count: int = Field(ge=0)


class CountryInsight(BaseModel):
    country: str
    top_category: str
    count: int = Field(ge=0)


class ScoreTrendPoint(BaseModel):
    date: str
    average_score: float = Field(ge=0, le=100)


class DashboardSummary(BaseModel):
    period_days: int
    total_analyses: int
    email_analyses: int
    meeting_analyses: int
    average_score: float
    manner_temperature: int
    scores: AnalysisScores
    country_usage: list[CountryUsage]
    country_insights: list[CountryInsight]
    frequent_issues: list[FrequentIssue]
    fixed_issues: list[FrequentIssue]
    score_trend: list[ScoreTrendPoint]
    accepted_suggestions: int
