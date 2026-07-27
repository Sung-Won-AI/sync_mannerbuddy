# 환경 변수 로딩: API 키는 .env 파일에서만 읽어오고 코드에 하드코딩하지 않는다.
# 확장/대시보드/백엔드가 모두 프로젝트 루트의 .env 하나를 공유해서 사용한다.

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, extra="ignore")

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    database_url: str = ""


settings = Settings()
