from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.admin import Admin
from app.schemas.auth import AdminRead, LoginRequest, TokenResponse
from app.services.auth_service import InvalidCredentialsError, authenticate_admin, issue_token_for

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        admin = authenticate_admin(db, payload.username, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        ) from exc
    return TokenResponse(access_token=issue_token_for(admin))


@router.get("/me", response_model=AdminRead)
def read_current_admin(admin: Admin = Depends(get_current_admin)) -> AdminRead:
    return AdminRead.model_validate(admin)
