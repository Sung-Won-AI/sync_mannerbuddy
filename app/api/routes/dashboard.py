from fastapi import APIRouter, Query

from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    period_days: int = Query(default=7, ge=1, le=90),
) -> DashboardSummary:
    return dashboard_service.get_summary(period_days)
