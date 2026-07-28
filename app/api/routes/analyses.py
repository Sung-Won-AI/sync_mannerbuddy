from fastapi import APIRouter, Header, Query, Request, status

from app.schemas.analysis import (
    AnalysisListResponse,
    EmailAnalysisRequest,
    EmailAnalysisResponse,
)
from app.schemas.feedback import AnalysisActionRequest, AnalysisActionResponse
from app.services.analysis_service import analysis_service

router = APIRouter()


@router.post(
    "/email",
    response_model=EmailAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_email(
    payload: EmailAnalysisRequest,
    request: Request,
    extension_version: str | None = Header(
        default=None,
        alias="X-Extension-Version",
    ),
) -> EmailAnalysisResponse:
    request_id = getattr(request.state, "request_id", None)
    return await analysis_service.analyze_email(
        payload=payload,
        request_id=request_id,
        extension_version=extension_version,
    )


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    kind: str | None = Query(default=None, pattern="^(email|meeting)$"),
    limit: int = Query(default=20, ge=1, le=50),
) -> AnalysisListResponse:
    return analysis_service.list_analyses(kind=kind, limit=limit)


@router.post(
    "/{analysis_id}/actions",
    response_model=AnalysisActionResponse,
)
async def save_analysis_action(
    analysis_id: str,
    payload: AnalysisActionRequest,
) -> AnalysisActionResponse:
    return analysis_service.save_action(analysis_id, payload)

