import os

os.environ["USE_MOCK_AI"] = "true"
os.environ["STORAGE_BACKEND"] = "memory"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import repository


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_repository():
    repository.reset()
    yield
    repository.reset()
