from __future__ import annotations

import datetime as dt

import bcrypt
import jwt

from app.config import settings

# bcrypt silently ignores bytes past 72; truncate explicitly so behavior is
# deterministic instead of depending on the underlying C library's quirks.
_MAX_BCRYPT_BYTES = 72


class TokenError(Exception):
    """Raised for any missing, malformed, tampered, or expired token."""


def _prepare(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_BCRYPT_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_prepare(password), password_hash.encode("utf-8"))


def create_access_token(subject: str, expires_delta: dt.timedelta | None = None) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    expire = now + (
        expires_delta
        if expires_delta is not None
        else dt.timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload = {"sub": subject, "iat": now, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError("invalid or expired token") from exc
