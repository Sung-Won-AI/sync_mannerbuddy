from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analyses import router as analyses_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.health import router as health_router
from app.api.routes.meetings import router as meetings_router
from app.api.routes.quizzes import router as quizzes_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Extension-Version",
            "X-Request-ID",
        ],
    )

    app.include_router(health_router)
    app.include_router(
        analyses_router,
        prefix=f"{settings.api_v1_prefix}/analyses",
        tags=["analyses"],
    )
    app.include_router(
        meetings_router,
        prefix=f"{settings.api_v1_prefix}/meetings",
        tags=["meetings"],
    )
    app.include_router(
        dashboard_router,
        prefix=f"{settings.api_v1_prefix}/dashboard",
        tags=["dashboard"],
    )
    app.include_router(
        quizzes_router,
        prefix=f"{settings.api_v1_prefix}/quizzes",
        tags=["quizzes"],
    )
    app.include_router(
        feedback_router,
        prefix=f"{settings.api_v1_prefix}/feedback",
        tags=["feedback"],
    )
    register_exception_handlers(app)
    return app


app = create_app()
