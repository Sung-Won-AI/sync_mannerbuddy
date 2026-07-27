from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from app.schemas.analysis import (
    AnalysisIssue,
    EmailAnalysisRequest,
    EmailAnalysisResponse,
)
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
        del extension_version  # Reserved for logging/persistence in the next step.
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

        return EmailAnalysisResponse(
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


analysis_service = AnalysisService()
