from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.login_event import LoginEvent


def create(
    db: Session, *, admin_id: int | None, username: str, success: bool, ip_address: str | None
) -> LoginEvent:
    event = LoginEvent(
        admin_id=admin_id, username=username, success=success, ip_address=ip_address
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_recent(db: Session, limit: int = 100) -> list[LoginEvent]:
    return list(
        db.execute(
            select(LoginEvent).order_by(LoginEvent.created_at.desc(), LoginEvent.id.desc()).limit(limit)
        ).scalars().all()
    )
