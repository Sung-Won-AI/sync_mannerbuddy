import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _read_origins() -> list[str]:
    raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development")
    app_name: str = os.getenv("APP_NAME", "Manner Buddy API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    allowed_origins: tuple[str, ...] = tuple(_read_origins())

    use_mock_ai: bool = _read_bool("USE_MOCK_AI", True)
    claude_api_key: str | None = os.getenv("CLAUDE_API_KEY") or None
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
    claude_effort: str = os.getenv("CLAUDE_EFFORT", "medium")

    max_email_characters: int = _read_int("MAX_EMAIL_CHARACTERS", 5000)
    analysis_timeout_seconds: int = _read_int(
        "ANALYSIS_TIMEOUT_SECONDS",
        60,
    )


settings = Settings()
