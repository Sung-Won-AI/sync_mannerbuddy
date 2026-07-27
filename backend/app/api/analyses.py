from fastapi import APIRouter, Header, Request, status

from app.schemas.analysis import EmailAnalysisRequest, EmailAnalysisResponse
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
