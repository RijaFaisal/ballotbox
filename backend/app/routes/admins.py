from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.admin import Admin
from app.repositories import admin_repository, login_event_repository
from app.routes.common import get_admin_or_404
from app.schemas.auth import AdminAccountCreate, AdminDeleteResult, AdminRead, LoginEventRead
from app.services.admin_account_service import (
    CannotDeleteLastAdminError,
    CannotDeleteSelfError,
    DuplicateAdminUsernameError,
    create_admin,
    delete_admin,
)

router = APIRouter(
    prefix="/admin/users", tags=["admin-users"], dependencies=[Depends(get_current_admin)]
)


@router.get("", response_model=list[AdminRead])
def list_admins(db: Session = Depends(get_db)) -> list[AdminRead]:
    return [
        AdminRead.model_validate(admin)
        for admin in admin_repository.list_all_ordered_by_username(db)
    ]


@router.get("/login-events", response_model=list[LoginEventRead])
def list_login_events(db: Session = Depends(get_db)) -> list[LoginEventRead]:
    return [
        LoginEventRead.model_validate(event)
        for event in login_event_repository.list_recent(db)
    ]


@router.post("", response_model=AdminRead, status_code=status.HTTP_201_CREATED)
def create_admin_account(payload: AdminAccountCreate, db: Session = Depends(get_db)) -> AdminRead:
    try:
        admin = create_admin(db, username=payload.username, password=payload.password)
    except DuplicateAdminUsernameError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An admin with this username already exists.",
        ) from exc
    return AdminRead.model_validate(admin)


@router.delete("/{admin_id}", response_model=AdminDeleteResult)
def delete_admin_account(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
) -> AdminDeleteResult:
    target = get_admin_or_404(db, admin_id)
    try:
        delete_admin(db, current_admin, target)
    except CannotDeleteSelfError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't delete your own admin account.",
        ) from exc
    except CannotDeleteLastAdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one admin account must always remain.",
        ) from exc
    return AdminDeleteResult()
