from abc import ABC, abstractmethod
from uuid import uuid4

import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError
from app.schemas.analysis import (
    AIAnalysisResult,
    AnalysisIssue,
    AnalysisScores,
    EmailAnalysisRequest,
)


class BaseAIClient(ABC):
    @abstractmethod
    async def analyze_email(
        self,
        *,
        masked_text: str,
        request: EmailAnalysisRequest,
    ) -> AIAnalysisResult:
        raise NotImplementedError


class MockAIClient(BaseAIClient):
    async def analyze_email(
        self,
        *,
        masked_text: str,
        request: EmailAnalysisRequest,
    ) -> AIAnalysisResult:
        example = "Please send the contract by Friday."
        if example in masked_text:
            start = masked_text.index(example)
            issue = AnalysisIssue(
                issue_id=str(uuid4()),
                original=example,
                start_index=start,
                end_index=start + len(example),
                category="tone",
                severity="medium",
                reason=(
                    f"{request.target_country.value} 비즈니스 환경에서는 "
                    "다소 직접적인 요청으로 들릴 수 있습니다."
                ),
                suggestion=(
                    "Would it be possible to send the contract by Friday?"
                ),
            )
            return AIAnalysisResult(
                overall_score=72,
                scores=AnalysisScores(
                    vocabulary=80,
                    tone=55,
                    taboo=90,
                    manners=65,
                ),
                issues=[issue],
                revised_text=masked_text.replace(
                    example,
                    issue.suggestion,
                    1,
                ),
                summary="요청 표현을 조금 더 간접적으로 조정하는 것이 좋습니다.",
            )

        return AIAnalysisResult(
            overall_score=85,
            scores=AnalysisScores(
                vocabulary=85,
                tone=85,
                taboo=90,
                manners=80,
            ),
            issues=[],
            revised_text=masked_text,
            summary="Mock 분석에서 뚜렷한 문화적 위험 표현을 찾지 못했습니다.",
        )


class RemoteAIClient(BaseAIClient):
    async def analyze_email(
        self,
        *,
        masked_text: str,
        request: EmailAnalysisRequest,
    ) -> AIAnalysisResult:
        if not settings.ai_service_url:
            raise AIServiceUnavailableError("AI_SERVICE_URL이 설정되지 않았습니다.")

        headers = {"Content-Type": "application/json"}
        if settings.ai_service_api_key:
            headers["Authorization"] = f"Bearer {settings.ai_service_api_key}"

        payload = {
            "text": masked_text,
            "target_country": request.target_country.value,
            "language": request.language,
        }

        try:
            async with httpx.AsyncClient(
                timeout=settings.analysis_timeout_seconds
            ) as client:
                response = await client.post(
                    f"{settings.ai_service_url.rstrip('/')}/analyze",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return AIAnalysisResult.model_validate(response.json())
        except (httpx.HTTPError, ValueError) as exc:
            raise AIServiceUnavailableError() from exc


def get_ai_client() -> BaseAIClient:
    if settings.use_mock_ai:
        return MockAIClient()
    return RemoteAIClient()

