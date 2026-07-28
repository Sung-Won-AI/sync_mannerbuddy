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

        restored_issues = [
            AnalysisIssue(
                **{
                    **issue.model_dump(),
                    "original": masking_service.restore(
                        issue.original,
                        masking_result.replacements,
                    ),
                    "suggestion": masking_service.restore(
                        issue.suggestion,
                        masking_result.replacements,
                    ),
                }
            )
            for issue in result.issues
        ]

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
