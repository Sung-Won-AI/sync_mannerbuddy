from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from app.core.config import settings
from app.repositories.memory_repository import repository
from app.schemas.analysis import AnalysisIssue, AnalysisScores, IssueSeverity
from app.schemas.meeting import (
    MeetingAnalysisRequest,
    MeetingAnalysisResponse,
    MeetingFlowPoint,
)
from app.services.ai_client import get_ai_client
from app.services.issue_resolution import resolve_and_restore_issues
from app.services.masking_service import masking_service

_SEVERITY_PENALTY = {
    IssueSeverity.LOW: 4,
    IssueSeverity.MEDIUM: 10,
    IssueSeverity.HIGH: 18,
}

# 매너 온도 = 4개 세부 점수의 가중평균. 이 제품의 핵심 가치(문화적 커뮤니케이션
# 리스크)에 맞춰 매너·어조를 가장 무겁게, 어휘는 가장 가볍게 반영한다.
_OVERALL_SCORE_WEIGHTS = {
    "manners": 0.30,
    "tone": 0.30,
    "taboo": 0.25,
    "vocabulary": 0.15,
}


def _compute_overall_score(scores: AnalysisScores) -> int:
    weighted = sum(
        getattr(scores, category) * weight
        for category, weight in _OVERALL_SCORE_WEIGHTS.items()
    )
    return round(weighted)


def _compute_flow(
    transcript_length: int,
    overall_score: int,
    issues: list[AnalysisIssue],
) -> list[MeetingFlowPoint]:
    segment_count = min(5, max(1, transcript_length // 200 + 1))
    segment_size = max(1, -(-transcript_length // segment_count))  # ceil division

    points: list[MeetingFlowPoint] = []
    for index in range(segment_count):
        seg_start = index * segment_size
        seg_end = transcript_length if index == segment_count - 1 else seg_start + segment_size
        penalty = sum(
            _SEVERITY_PENALTY.get(issue.severity, 8)
            for issue in issues
            if seg_start <= issue.start_index < seg_end
        )
        temperature = max(20, min(100, overall_score - penalty))
        points.append(
            MeetingFlowPoint(
                segment=index + 1,
                temperature=temperature,
                label=f"구간 {index + 1}",
            )
        )
    return points


class MeetingService:
    async def analyze_transcript(
        self,
        *,
        payload: MeetingAnalysisRequest,
        request_id: str | None,
    ) -> MeetingAnalysisResponse:
        started_at = perf_counter()

        masking_result = masking_service.mask(payload.transcript)
        result = await get_ai_client().analyze_meeting(
            masked_transcript=masking_result.masked_text,
            request=payload,
        )

        restored_issues = resolve_and_restore_issues(
            original_text=payload.transcript,
            replacements=masking_result.replacements,
            issues=result.issues,
        )
        overall_score = _compute_overall_score(result.scores)

        flow = _compute_flow(
            len(payload.transcript),
            overall_score,
            restored_issues,
        )

        response = MeetingAnalysisResponse(
            analysis_id=str(uuid4()),
            title=payload.title,
            overall_score=overall_score,
            meeting_temperature=overall_score,
            scores=result.scores,
            issues=restored_issues,
            summary=result.summary,
            key_points=result.key_points,
            action_items=result.action_items,
            flow=flow,
            request_id=request_id,
            processing_time_ms=round((perf_counter() - started_at) * 1000),
            created_at=datetime.now(UTC).isoformat(),
        )
        repository.save_analysis(
            {
                **response.model_dump(mode="json"),
                "created_at": datetime.fromisoformat(response.created_at),
                "user_id": settings.demo_user_id,
                "kind": "meeting",
                "target_country": payload.target_country.value,
                "client_request_id": payload.client_request_id,
            }
        )
        return response


meeting_service = MeetingService()
