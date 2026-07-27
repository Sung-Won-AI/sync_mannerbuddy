from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, meeting_summary, review_quiz
from app.api.analyses import router as analyses_router
from app.api.health import router as health_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_origin_regex=r"chrome-extension://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(
        analyses_router,
        prefix=f"{settings.api_v1_prefix}/analyses",
        tags=["analyses"],
    )
    # [기능 2~4] 회의 요약 / 대시보드 / 복습·퀴즈: 아직 스텁 상태, 이번 병합 범위 밖.
    app.include_router(meeting_summary.router)
    app.include_router(dashboard.router)
    app.include_router(review_quiz.router)

    register_exception_handlers(app)
    return app


app = create_app()
