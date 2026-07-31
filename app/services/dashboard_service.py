from collections import defaultdict
from statistics import mean

from app.core.config import settings
from app.repositories.memory_repository import repository
from app.schemas.analysis import AnalysisScores
from app.schemas.dashboard import (
    CountryUsage,
    DashboardSummary,
    FrequentIssue,
    ScoreTrendPoint,
)


class DashboardService:
    def get_summary(self, period_days: int) -> DashboardSummary:
        data = repository.dashboard(settings.demo_user_id, period_days)
        records = data["records"]
        if not records:
            return DashboardSummary(
                period_days=period_days,
                total_analyses=0,
                email_analyses=0,
                meeting_analyses=0,
                average_score=0,
                manner_temperature=0,
                scores=AnalysisScores(
                    vocabulary=0,
                    tone=0,
                    taboo=0,
                    manners=0,
                ),
                country_usage=[],
                frequent_issues=[],
                score_trend=[],
                accepted_suggestions=0,
            )

        average_score = round(mean(r["overall_score"] for r in records), 1)
        score_names = ("vocabulary", "tone", "taboo", "manners")
        score_values = {
            name: round(mean(r["scores"][name] for r in records))
            for name in score_names
        }
        by_date: dict[str, list[int]] = defaultdict(list)
        for record in records:
            by_date[record["created_at"].date().isoformat()].append(
                record["overall_score"]
            )

        return DashboardSummary(
            period_days=period_days,
            total_analyses=len(records),
            email_analyses=sum(r["kind"] == "email" for r in records),
            meeting_analyses=sum(r["kind"] == "meeting" for r in records),
            average_score=average_score,
            manner_temperature=round(average_score),
            scores=AnalysisScores(**score_values),
            country_usage=[
                CountryUsage(country=country, count=count)
                for country, count in data["country_counts"].most_common()
            ],
            frequent_issues=[
                FrequentIssue(category=str(category), count=count)
                for category, count in data["issue_counts"].most_common(4)
            ],
            score_trend=[
                ScoreTrendPoint(
                    date=date,
                    average_score=round(mean(scores), 1),
                )
                for date, scores in sorted(by_date.items())
            ],
            accepted_suggestions=data["accepted_suggestions"],
        )


dashboard_service = DashboardService()

