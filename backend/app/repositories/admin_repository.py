from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.admin import Admin


def get_by_username(db: Session, username: str) -> Admin | None:
    return db.execute(
        select(Admin).where(Admin.username == username)
    ).scalar_one_or_none()
