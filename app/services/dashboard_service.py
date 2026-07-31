from collections import Counter, defaultdict
from statistics import mean

from app.core.config import settings
from app.repositories import repository
from app.schemas.analysis import AnalysisScores
from app.schemas.dashboard import (
    CountryInsight,
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
                country_insights=[],
                frequent_issues=[],
                fixed_issues=[],
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

        # 국가별로 가장 자주 감지된 카테고리 하나씩 — "이번주 나의 비즈니스 매너는?"
        # 인사이트 카드가 국가별로 실제 데이터에 기반한 코멘트를 보여줄 수 있게 한다.
        country_category_counts: dict[str, Counter] = defaultdict(Counter)
        for record in records:
            for issue in record.get("issues", []):
                country_category_counts[record["target_country"]][
                    issue["category"]
                ] += 1

        country_insights = [
            CountryInsight(
                country=country,
                top_category=str(category_counts.most_common(1)[0][0]),
                count=category_counts.most_common(1)[0][1],
            )
            for country, _ in data["country_counts"].most_common()
            if (category_counts := country_category_counts.get(country))
        ]

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
            country_insights=country_insights,
            frequent_issues=[
                FrequentIssue(category=str(category), count=count)
                for category, count in data["issue_counts"].most_common(4)
            ],
            fixed_issues=[
                FrequentIssue(category=str(category), count=count)
                for category, count in data["fixed_issue_counts"].most_common(4)
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

