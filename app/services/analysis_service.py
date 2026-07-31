from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from app.schemas.analysis import (
    AnalysisIssue,
    AnalysisListItem,
    AnalysisListResponse,
    EmailAnalysisRequest,
    EmailAnalysisResponse,
)
from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError
from app.repositories.memory_repository import repository
from app.schemas.feedback import AnalysisActionRequest, AnalysisActionResponse
from app.services.ai_client import get_ai_client
from app.services.masking_service import masking_service


def _drop_overlapping_issues(issues: list[AnalysisIssue]) -> list[AnalysisIssue]:
    # AI가 "문장 전체를 다시 쓰는" issue와 그 안에 포함된 단어 단위 issue(예: "pls")를
    # 함께 반환할 때가 있다. 겹치는 채로 둘 다 하이라이트하면 프론트엔드에서 하이라이트
    # span이 서로 안에 중첩되어 오프셋 계산이 깨지므로, 넓은 범위를 우선하고 그 안에
    # 겹치는 좁은 issue는 버린다.
    widest_first = sorted(
        issues,
        key=lambda issue: issue.end_index - issue.start_index,
        reverse=True,
    )
    kept: list[AnalysisIssue] = []
    for issue in widest_first:
        overlaps = any(
            issue.start_index < k.end_index and issue.end_index > k.start_index
            for k in kept
        )
        if not overlaps:
            kept.append(issue)
    return sorted(kept, key=lambda issue: issue.start_index)


class AnalysisService:
    async def analyze_email(
        self,
        *,
        payload: EmailAnalysisRequest,
        request_id: str | None,
        extension_version: str | None,
    ) -> EmailAnalysisResponse:
        started_at = perf_counter()

        masking_result = masking_service.mask(payload.text)
        result = await get_ai_client().analyze_email(
            masked_text=masking_result.masked_text,
            request=payload,
        )

        restored_issues = []
        for issue in result.issues:
            restored_original = masking_service.restore(
                issue.original,
                masking_result.replacements,
            )
            # AI가 직접 센 문자 오프셋은 (특히 텍스트가 길어질수록) 어긋나기 쉬우니,
            # AI가 그대로 베껴 적은 original 문구를 원문에서 다시 찾아 오프셋을
            # 신뢰할 수 있게 재계산한다. 못 찾으면(패러프레이즈 등) AI 오프셋으로 폴백.
            found_at = payload.text.find(restored_original)
            start_index = found_at if found_at != -1 else issue.start_index
            end_index = (
                found_at + len(restored_original)
                if found_at != -1
                else issue.end_index
            )

            restored_issues.append(
                AnalysisIssue(
                    **{
                        **issue.model_dump(),
                        "original": restored_original,
                        "suggestion": masking_service.restore(
                            issue.suggestion,
                            masking_result.replacements,
                        ),
                        "start_index": start_index,
                        "end_index": end_index,
                    }
                )
            )

        restored_issues = _drop_overlapping_issues(restored_issues)

        response = EmailAnalysisResponse(
            analysis_id=str(uuid4()),
            request_id=request_id,
            overall_score=result.overall_score,
            scores=result.scores,
            issues=restored_issues,
            revised_text=masking_service.restore(
                result.revised_text,
                masking_result.replacements,
            ),
            summary=result.summary,
            processing_time_ms=round((perf_counter() - started_at) * 1000),
            created_at=datetime.now(UTC),
        )
        repository.save_analysis(
            {
                **response.model_dump(mode="json"),
                "created_at": response.created_at,
                "user_id": settings.demo_user_id,
                "kind": "email",
                "target_country": payload.target_country.value,
                "extension_version": extension_version,
                "client_request_id": payload.client_request_id,
            }
        )
        return response

    def list_analyses(
        self,
        *,
        kind: str | None,
        limit: int,
    ) -> AnalysisListResponse:
        records = repository.list_analyses(
            settings.demo_user_id,
            kind=kind,
            limit=limit,
        )
        items = [
            AnalysisListItem(
                analysis_id=record["analysis_id"],
                kind=record["kind"],
                target_country=record["target_country"],
                overall_score=record["overall_score"],
                summary=record["summary"],
                created_at=record["created_at"],
            )
            for record in records
        ]
        return AnalysisListResponse(items=items, total=len(items))

    def save_action(
        self,
        analysis_id: str,
        payload: AnalysisActionRequest,
    ) -> AnalysisActionResponse:
        analysis = repository.get_analysis(
            analysis_id,
            settings.demo_user_id,
        )
        if analysis is None:
            raise ResourceNotFoundError("분석 결과")

        issue_ids = {
            issue["issue_id"]
            for issue in analysis.get("issues", [])
        }
        if payload.issue_id not in issue_ids:
            raise ResourceNotFoundError("분석 문제")

        repository.save_action(
            {
                "user_id": settings.demo_user_id,
                "analysis_id": analysis_id,
                "issue_id": payload.issue_id,
                "action": payload.action.value,
            }
        )
        return AnalysisActionResponse(
            saved=True,
            analysis_id=analysis_id,
            issue_id=payload.issue_id,
            action=payload.action,
        )


analysis_service = AnalysisService()
