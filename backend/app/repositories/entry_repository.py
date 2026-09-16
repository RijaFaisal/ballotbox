from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entry import Entry


def get_by_identifier(db: Session, identifier: str) -> Entry | None:
    return db.execute(
        select(Entry).where(Entry.identifier == identifier)
    ).scalar_one_or_none()


def create(db: Session, name: str, identifier: str) -> Entry:
    entry = Entry(name=name, identifier=identifier)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_all_ordered_by_id(db: Session) -> list[Entry]:
    return list(db.execute(select(Entry).order_by(Entry.id)).scalars().all())
