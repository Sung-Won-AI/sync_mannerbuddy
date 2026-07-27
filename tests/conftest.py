import os

os.environ["USE_MOCK_AI"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

