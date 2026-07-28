from fastapi import APIRouter, Request

from app.schemas.meeting import MeetingAnalysisRequest, MeetingAnalysisResponse
from app.services.meeting_service import meeting_service

router = APIRouter()


@router.post("/transcript", response_model=MeetingAnalysisResponse)
async def analyze_meeting_transcript(
    payload: MeetingAnalysisRequest,
    request: Request,
) -> MeetingAnalysisResponse:
    return await meeting_service.analyze_transcript(
        payload=payload,
        request_id=getattr(request.state, "request_id", None),
    )
