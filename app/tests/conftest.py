import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Tests always use the dedicated CI database, never a developer or production DB.
APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/focus_journal_test"
)
os.environ["SECRET_KEY"] = "test-secret-key-use-only-in-automated-tests-123456"
os.environ["SESSION_SECRET_KEY"] = "test-session-secret-use-only-in-automated-tests-123"
os.environ["SESSION_COOKIE_SECURE"] = "false"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ["FRONTEND_BASE_URL"] = "http://localhost:5173"
# Automated tests must never send journal text to an external AI provider.
os.environ["OPENAI_API_KEY"] = ""


@pytest.fixture(scope="session")
def client():
    from main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def user_factory(client):
    def create_user():
        import uuid

        email = f"focus-journal-{uuid.uuid4().hex}@example.com"
        password = "StrongPass1!"
        registration = client.post(
            "/auth/register",
            json={
                "email": email,
                "name": "Focus Journal Tester",
                "password": password,
                "confirm_password": password,
            },
        )
        assert registration.status_code == 201, registration.text
        login = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200, login.text
        payload = login.json()
        assert payload["access_token"]
        return {
            "email": email,
            "password": password,
            "user_id": registration.json()["user_id"],
            "token": payload["access_token"],
            "headers": {"Authorization": f"Bearer {payload['access_token']}"},
        }

    return create_user
