import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings
from app.database.database import get_db

bearer = HTTPBearer()


def _decode_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=["HS256"],
        options={"require_exp": True, "require_sub": True, "require_jti": True},
    )
    if not payload.get("jti"):
        raise JWTError("Token identifier is missing.")
    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> int:
    try:
        payload = _decode_token(credentials.credentials)
        user_id = int(payload["sub"])
        token_id = str(payload["jti"])
        expires_at = int(payload["exp"])
    except (JWTError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None

    with get_db() as db:
        revoked = db.execute(
            "SELECT 1 FROM revoked_tokens WHERE token_id=? AND expires_at>?",
            (token_id, int(time.time())),
        ).fetchone()
    if revoked or expires_at <= int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user_id


def revoke_access_token(token: str) -> None:
    try:
        payload = _decode_token(token)
        token_id = str(payload["jti"])
        expires_at = int(payload["exp"])
    except (JWTError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None

    with get_db() as db:
        now = int(time.time())
        db.execute("DELETE FROM revoked_tokens WHERE expires_at<=?", (now,))
        db.execute(
            "INSERT OR REPLACE INTO revoked_tokens(token_id,expires_at) VALUES(?,?)",
            (token_id, expires_at),
        )
