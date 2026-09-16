from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenError, decode_access_token
from app.database import get_db
from app.models.admin import Admin
from app.repositories import admin_repository

_bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Admin:
    if credentials is None:
        raise _UNAUTHORIZED

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenError as exc:
        raise _UNAUTHORIZED from exc

    username = payload.get("sub")
    if not username:
        raise _UNAUTHORIZED

    admin = admin_repository.get_by_username(db, username)
    if admin is None:
        raise _UNAUTHORIZED

    return admin
