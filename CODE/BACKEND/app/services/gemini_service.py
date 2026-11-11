"""Small, low-token Gemini service with bounded retries and response caching."""

from __future__ import annotations

import hashlib
import json
import random
import threading
import time
from collections import OrderedDict, deque
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from google import genai
from google.genai import types

from app.config import settings

P = ParamSpec("P")
R = TypeVar("R")
CACHE_TTL_SECONDS = 300
CACHE_MAX_ENTRIES = 128
MAX_RETRY_ATTEMPTS = 3
MAX_REQUESTS_PER_MINUTE = 15


class _ResponseCache:
    def __init__(self) -> None:
        self._entries: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> str | None:
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= now:
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return value

    def put(self, key: str, value: str) -> None:
        with self._lock:
            self._entries[key] = (time.monotonic() + CACHE_TTL_SECONDS, value)
            self._entries.move_to_end(key)
            while len(self._entries) > CACHE_MAX_ENTRIES:
                self._entries.popitem(last=False)


class _RequestRateLimiter:
    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            while True:
                now = time.monotonic()
                while self._calls and now - self._calls[0] >= 60:
                    self._calls.popleft()
                if len(self._calls) < self._limit:
                    self._calls.append(now)
                    return
                time.sleep(max(0.01, 60 - (now - self._calls[0])))


_response_cache = _ResponseCache()
_request_rate_limiter = _RequestRateLimiter(MAX_REQUESTS_PER_MINUTE)


def _status_code(error: Exception) -> int | None:
    code: object = getattr(error, "code", None) or getattr(
        error, "status_code", None
    )
    if callable(code):
        code = code()
    if code is None:
        response = getattr(error, "response", None)
        code = getattr(response, "status_code", None)
    if isinstance(code, int):
        return code
    if not isinstance(code, str):
        return None
    try:
        return int(code)
    except (TypeError, ValueError):
        return None


def _retry_after(error: Exception) -> float | None:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {})
    value = headers.get("Retry-After") or headers.get("retry-after")
    try:
        return max(0.0, float(value)) if value is not None else None
    except (TypeError, ValueError):
        return None


def _is_retryable(error: Exception) -> bool:
    code = _status_code(error)
    transient_transport_errors = {
        "ConnectError",
        "ConnectTimeout",
        "ReadTimeout",
        "TimeoutException",
        "WriteTimeout",
    }
    return (
        code == 429
        or code in {500, 502, 503, 504}
        or isinstance(error, (TimeoutError, ConnectionError))
        or error.__class__.__name__ in transient_transport_errors
    )


def retry_transient(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                _request_rate_limiter.acquire()
                return func(*args, **kwargs)
            except Exception as exc:
                if not _is_retryable(exc) or attempt == MAX_RETRY_ATTEMPTS - 1:
                    raise
                retry_after = _retry_after(exc)
                delay = retry_after if retry_after is not None else 0.5 * (2**attempt)
                time.sleep(delay + random.uniform(0, 0.2))
        raise RuntimeError("Gemini retry loop ended unexpectedly.")

    return wrapped


class GeminiService:
    def __init__(self) -> None:
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(
                api_key=settings.gemini_api_key.get_secret_value()
            )
        return self._client

    @staticmethod
    def _cache_key(
        prompt: str,
        system_instruction: str | None,
        temperature: float,
        max_output_tokens: int,
        use_search: bool,
    ) -> str:
        request = json.dumps(
            [
                settings.gemini_model,
                settings.gemini_fallback_model,
                prompt,
                system_instruction,
                temperature,
                max_output_tokens,
                use_search,
            ],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(request.encode("utf-8")).hexdigest()

    @retry_transient
    def _generate_content(
        self,
        *,
        model: str,
        prompt: str,
        config: types.GenerateContentConfig,
    ) -> Any:
        return self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

    def _generate_text(
        self,
        prompt: str,
        *,
        system_instruction: str | None,
        temperature: float,
        max_output_tokens: int,
        use_search: bool,
    ) -> str:
        key = self._cache_key(
            prompt,
            system_instruction,
            temperature,
            max_output_tokens,
            use_search,
        )
        cached = _response_cache.get(key)
        if cached is not None:
            return cached

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
            tools=(
                [types.Tool(google_search=types.GoogleSearch())]
                if use_search
                else None
            ),
        )
        models = [settings.gemini_model]
        fallback_model = settings.gemini_fallback_model.strip()
        if fallback_model and fallback_model not in models:
            models.append(fallback_model)

        last_error: Exception | None = None
        for model in models:
            try:
                response = self._generate_content(
                    model=model,
                    prompt=prompt,
                    config=config,
                )
                text = (response.text or "").strip()
                if text:
                    _response_cache.put(key, text)
                return text
            except Exception as exc:
                last_error = exc
                if model == models[-1]:
                    raise

        if last_error is not None:
            raise last_error
        raise RuntimeError("Gemini did not return a response.")

    def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int = 700,
    ) -> str:
        return self._generate_text(
            prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            use_search=False,
        )

    def research(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int = 900,
    ) -> str:
        """One small grounded search call for current public market context."""
        return self._generate_text(
            prompt,
            system_instruction=system_instruction,
            temperature=0.1,
            max_output_tokens=max_output_tokens,
            use_search=True,
        )

    def generate_json(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int = 700,
    ) -> dict[str, Any]:
        text = self.generate(
            prompt,
            system_instruction=system_instruction,
            temperature=0.1,
            max_output_tokens=max_output_tokens,
        )
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3].strip()
        value = json.loads(cleaned)
        if not isinstance(value, dict):
            raise RuntimeError("Gemini JSON response must be an object.")
        return value


gemini_service = GeminiService()
