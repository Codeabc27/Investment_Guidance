from datetime import datetime, timedelta, timezone
import uuid

import bcrypt
from jose import jwt
from app.config import settings
from app.database.database import get_db


BCRYPT_ROUNDS = 12


def hash_password(password):
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must be no more than 72 UTF-8 bytes.")
    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
    ).decode()

def verify_password(password, password_hash):
    try:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            return False
        return bcrypt.checkpw(password_bytes, password_hash.encode())
    except (TypeError, ValueError):
        return False

def create_access_token(user_id):
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {
            "sub": str(user_id),
            "jti": str(uuid.uuid4()),
            "iat": datetime.now(timezone.utc),
            "exp": expires_at,
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )

def register_user(email, password):
    with get_db() as db:
        if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
            raise ValueError("Email already registered")
        cur = db.execute("INSERT INTO users(email,password_hash) VALUES(?,?)", (email, hash_password(password)))
        return {"id": cur.lastrowid, "email": email}

def authenticate_user(email, password):
    with get_db() as db:
        row = db.execute("SELECT id,email,password_hash FROM users WHERE email=?", (email,)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "email": row["email"]}
