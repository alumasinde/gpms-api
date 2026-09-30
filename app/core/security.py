from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()
password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(*, user_id: str, organization_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "org": organization_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(*, user_id: str, organization_id: str) -> tuple[str, str, datetime]:
    raw = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.refresh_token_expire_days)
    return raw, hash_token(raw), expires_at


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def hash_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
