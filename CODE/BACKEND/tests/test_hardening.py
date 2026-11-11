import os
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from jose import jwt
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "BACKEND"))
os.environ.setdefault("SECRET_KEY", "local-test-secret-that-is-long-enough-123456")
os.environ.setdefault("DATABASE_URL", "sqlite:///./DATA_BASE/investment.db")
os.environ.setdefault("GEMINI_API_KEY", "local-test-gemini-key")

from app.config import Settings, settings
from app.services import security
from app.services.auth_service import BCRYPT_ROUNDS, create_access_token, hash_password, verify_password
from app.services.gemini_service import GeminiService, retry_transient
from app.workflow.state import merge_state


def test_state_reducer_merges_parallel_nested_updates():
    merged = merge_state(
        {"analysis": {"goal": {"name": "Home"}, "status": "pending"}},
        {"analysis": {"risk": {"category": "Moderate"}, "status": "complete"}},
    )
    assert merged == {
        "analysis": {
            "goal": {"name": "Home"},
            "risk": {"category": "Moderate"},
            "status": "complete",
        }
    }


def test_retry_decorator_retries_rate_limit(monkeypatch):
    attempts = 0

    class RateLimitError(Exception):
        code = 429

    monkeypatch.setattr(
        "app.services.gemini_service._request_rate_limiter.acquire", lambda: None
    )
    monkeypatch.setattr("app.services.gemini_service.time.sleep", lambda _: None)

    @retry_transient
    def request():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RateLimitError()
        return "ok"

    assert request() == "ok"
    assert attempts == 3


def test_gemini_successful_responses_are_cached(monkeypatch):
    service = GeminiService()
    calls = 0

    def generate_content(**_kwargs):
        nonlocal calls
        assert _kwargs["model"] == settings.gemini_model
        calls += 1
        return SimpleNamespace(text="cached response")

    monkeypatch.setattr(service, "_generate_content", generate_content)
    prompt = f"cache-test-{uuid4()}"
    assert service.generate(prompt) == "cached response"
    assert service.generate(prompt) == "cached response"
    assert calls == 1


def test_password_hash_uses_configured_work_factor():
    password_hash = hash_password("safe-passphrase-123")
    assert password_hash.split("$")[2] == str(BCRYPT_ROUNDS) == "12"
    assert verify_password("safe-passphrase-123", password_hash)
    assert not verify_password("different-passphrase", password_hash)


def test_access_token_can_be_revoked(monkeypatch):
    revoked_tokens: set[str] = set()

    class FakeDatabase:
        def execute(self, query, params=()):
            if query.startswith("SELECT 1 FROM revoked_tokens"):
                return SimpleNamespace(
                    fetchone=lambda: (1,) if params[0] in revoked_tokens else None
                )
            if query.startswith("INSERT OR REPLACE INTO revoked_tokens"):
                revoked_tokens.add(params[0])
            return SimpleNamespace(fetchone=lambda: None)

    @contextmanager
    def fake_get_db():
        yield FakeDatabase()

    monkeypatch.setattr(security, "get_db", fake_get_db)
    token = create_access_token(42)
    credentials = security.HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    assert security.get_current_user(credentials) == 42
    security.revoke_access_token(token)
    with pytest.raises(HTTPException) as error:
        security.get_current_user(credentials)
    assert error.value.status_code == 401


def test_expired_tokens_are_rejected(monkeypatch):
    @contextmanager
    def unexpected_database_access():
        pytest.fail("Expired tokens must be rejected before database access.")
        yield

    monkeypatch.setattr(security, "get_db", unexpected_database_access)
    token = jwt.encode(
        {
            "sub": "42",
            "jti": "expired-test-token",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )
    credentials = security.HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )
    with pytest.raises(HTTPException) as error:
        security.get_current_user(credentials)
    assert error.value.status_code == 401


def test_settings_reject_missing_secrets_and_wildcard_cors():
    assert Settings.model_fields["secret_key"].is_required()
    assert Settings.model_fields["database_url"].is_required()
    assert Settings.model_fields["gemini_api_key"].is_required()
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "secret_key": "local-test-secret-that-is-long-enough-123456",
                "database_url": "sqlite:///./DATA_BASE/investment.db",
                "gemini_api_key": "local-test-gemini-key",
                "frontend_origin": "*",
            }
        )
