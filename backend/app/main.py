from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, email_correction, meeting_summary, review_quiz

app = FastAPI(title="MannerBuddy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_origin_regex=r"chrome-extension://.*",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(email_correction.router)
app.include_router(meeting_summary.router)
app.include_router(dashboard.router)
app.include_router(review_quiz.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
