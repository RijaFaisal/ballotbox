from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.admin import Admin
from app.repositories import admin_repository, login_event_repository
from app.schemas.auth import AdminRead, LoginRequest, TokenResponse
from app.services.auth_service import InvalidCredentialsError, authenticate_admin, issue_token_for

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    ip_address = request.client.host if request.client else None
    # Looked up independently of authenticate_admin's own internal lookup so
    # a failed attempt against a real username still logs which admin it
    # targeted. This runs for every attempt regardless of outcome, so it
    # can't reintroduce the username-existence timing signal
    # authenticate_admin's dummy-hash comparison guards against.
    existing_admin = admin_repository.get_by_username(db, payload.username)

    try:
        admin = authenticate_admin(db, payload.username, payload.password)
    except InvalidCredentialsError as exc:
        login_event_repository.create(
            db,
            admin_id=existing_admin.id if existing_admin else None,
            username=payload.username,
            success=False,
            ip_address=ip_address,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        ) from exc

    login_event_repository.create(
        db, admin_id=admin.id, username=admin.username, success=True, ip_address=ip_address
    )
    return TokenResponse(access_token=issue_token_for(admin))


@router.get("/me", response_model=AdminRead)
def read_current_admin(admin: Admin = Depends(get_current_admin)) -> AdminRead:
    return AdminRead.model_validate(admin)
