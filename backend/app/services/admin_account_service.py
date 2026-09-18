from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.admin import Admin
from app.repositories import admin_repository


class DuplicateAdminUsernameError(Exception):
    pass


class CannotDeleteSelfError(Exception):
    pass


class CannotDeleteLastAdminError(Exception):
    pass


def create_admin(db: Session, username: str, password: str) -> Admin:
    if admin_repository.get_by_username(db, username) is not None:
        raise DuplicateAdminUsernameError()
    try:
        return admin_repository.create(db, username=username, password_hash=hash_password(password))
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateAdminUsernameError() from exc


def delete_admin(db: Session, current_admin: Admin, target: Admin) -> None:
    """Guards against locking every admin out of the dashboard: you can
    never delete your own account through this UI, and the last remaining
    admin account can never be deleted."""
    if target.id == current_admin.id:
        raise CannotDeleteSelfError()
    if admin_repository.count_all(db) <= 1:
        raise CannotDeleteLastAdminError()
    admin_repository.delete(db, target)
