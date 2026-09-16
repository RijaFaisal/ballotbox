from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.admin import Admin
from app.repositories import admin_repository

# Fixed dummy hash checked when the username doesn't exist, so verifying an
# unknown username costs the same bcrypt work as verifying a wrong password.
# Without this, response time alone would reveal whether a username exists.
_DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-timing-parity")


class InvalidCredentialsError(Exception):
    pass


def authenticate_admin(db: Session, username: str, password: str) -> Admin:
    admin = admin_repository.get_by_username(db, username)
    password_hash = admin.password_hash if admin is not None else _DUMMY_PASSWORD_HASH

    if not verify_password(password, password_hash) or admin is None:
        raise InvalidCredentialsError()

    return admin


def issue_token_for(admin: Admin) -> str:
    return create_access_token(subject=admin.username)
