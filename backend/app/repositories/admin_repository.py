from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.admin import Admin


def get_by_username(db: Session, username: str) -> Admin | None:
    return db.execute(
        select(Admin).where(func.lower(Admin.username) == username.lower())
    ).scalar_one_or_none()


def get_by_id(db: Session, admin_id: int) -> Admin | None:
    return db.execute(select(Admin).where(Admin.id == admin_id)).scalar_one_or_none()


def list_all_ordered_by_username(db: Session) -> list[Admin]:
    return list(db.execute(select(Admin).order_by(func.lower(Admin.username))).scalars().all())


def create(db: Session, username: str, password_hash: str) -> Admin:
    admin = Admin(username=username, password_hash=password_hash)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def delete(db: Session, admin: Admin) -> None:
    db.delete(admin)
    db.commit()


def count_all(db: Session) -> int:
    return db.execute(select(func.count()).select_from(Admin)).scalar_one()
