import os

os.environ.setdefault("OTP_ENABLED", "false")
os.environ.setdefault("OTP_DEV_MODE", "true")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_client(client):
    response = client.post("/api/session", json={"mobile": "9123456789"})
    assert response.status_code == 200
    return client
