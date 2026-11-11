from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "Investment Guidance AI"
    app_version: str = "3.0.0"
    debug: bool = True

    secret_key: SecretStr = Field(min_length=32)
    database_url: str = Field(min_length=1)
    access_token_expire_minutes: int = Field(default=60, gt=0)

    gemini_api_key: SecretStr = Field(min_length=1)
    gemini_model: str = "gemini-3.6-flash"
    gemini_fallback_model: str = ""
    frontend_origin: str = "http://127.0.0.1:5000"

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value().strip()
        if secret.lower().startswith(("replace-", "your-", "change-me")):
            raise ValueError("SECRET_KEY must be replaced with a random secret.")
        return value

    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_api_key(cls, value: SecretStr) -> SecretStr:
        key = value.get_secret_value().strip()
        if key.lower().startswith(("replace-", "your-", "change-me")):
            raise ValueError("GEMINI_API_KEY must be a configured API key.")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        try:
            parsed = make_url(value)
        except (ArgumentError, ValueError) as exc:
            raise ValueError("DATABASE_URL must be a valid SQLite URL.") from exc
        if parsed.drivername != "sqlite" or not parsed.database:
            raise ValueError("DATABASE_URL must point to a persistent SQLite database.")
        if parsed.database == ":memory:":
            raise ValueError("DATABASE_URL must use a persistent SQLite database.")
        return value

    @field_validator("frontend_origin")
    @classmethod
    def validate_frontend_origin(cls, value: str) -> str:
        parsed = urlsplit(value)
        try:
            parsed.port
        except ValueError as exc:
            raise ValueError("FRONTEND_ORIGIN must use a valid port.") from exc
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or "*" in value
            or parsed.username
            or parsed.password
        ):
            raise ValueError("FRONTEND_ORIGIN must be one explicit HTTP(S) origin.")
        return value.rstrip("/")

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def jwt_secret_key(self) -> str:
        return self.secret_key.get_secret_value()


settings = Settings()  # type: ignore[call-arg]  # Required settings load from environment or .env.

database_location = make_url(settings.database_url).database
if database_location is None:
    raise ValueError("DATABASE_URL must include a database file path.")
DATABASE_PATH = Path(database_location)
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = BASE_DIR / DATABASE_PATH
DATABASE_DIR = DATABASE_PATH.parent
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
