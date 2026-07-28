from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from app.core.config import settings
from app.repositories.memory_repository import repository
from app.schemas.analysis import AnalysisIssue, AnalysisScores
from app.schemas.meeting import (
    MeetingAnalysisRequest,
    MeetingAnalysisResponse,
    MeetingFlowPoint,
)
from app.services.masking_service import masking_service


class MeetingService:
    async def analyze_transcript(
        self,
        *,
        payload: MeetingAnalysisRequest,
        request_id: str | None,
    ) -> MeetingAnalysisResponse:
        started_at = perf_counter()
        masked = masking_service.mask(payload.transcript)

        direct_phrases = (
            "you are wrong",
            "that's wrong",
            "do it now",
            "you must",
        )
        issues: list[AnalysisIssue] = []
        lowered = masked.masked_text.lower()
        for phrase in direct_phrases:
            start = lowered.find(phrase)
            if start < 0:
                continue
            original = masked.masked_text[start : start + len(phrase)]
            issues.append(
                AnalysisIssue(
                    issue_id=str(uuid4()),
                    original=original,
                    start_index=start,
                    end_index=start + len(phrase),
                    category="tone",
                    severity="medium",
                    reason="직접적인 반박이나 명령으로 받아들여질 수 있습니다.",
                    suggestion="Could we consider another perspective?",
                )
            )

        penalty = min(40, len(issues) * 12)
        overall = 88 - penalty
        scores = AnalysisScores(
            vocabulary=86,
            tone=max(40, 88 - penalty),
            taboo=92,
            manners=max(45, 86 - penalty),
        )
        segment_count = min(5, max(1, len(payload.transcript) // 80 + 1))
        flow = [
            MeetingFlowPoint(
                segment=index + 1,
                temperature=max(40, overall + (index % 3 - 1) * 4),
                label=f"구간 {index + 1}",
            )
            for index in range(segment_count)
        ]
        response = MeetingAnalysisResponse(
            analysis_id=str(uuid4()),
            title=payload.title,
            overall_score=overall,
            meeting_temperature=overall,
            scores=scores,
            issues=issues,
            summary=(
                "회의의 핵심 논의와 문화적 커뮤니케이션 위험을 분석했습니다."
            ),
            key_points=[
                "참석자들이 일정과 업무 우선순위를 논의했습니다.",
                "직접적인 표현은 완곡한 제안형 표현으로 바꾸는 것이 좋습니다.",
            ],
            action_items=[
                "담당자와 완료 기한을 다시 확인합니다.",
                "후속 이메일에서 결정 사항을 정리합니다.",
            ],
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

