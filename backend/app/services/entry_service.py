from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entry import Entry
from app.repositories import ballot_settings_repository, entry_repository
from app.schemas.entry import EntryCreate


class DuplicateEntryError(Exception):
    pass


class BallotClosedError(Exception):
    pass


def submit_entry(db: Session, payload: EntryCreate) -> Entry:
    if not ballot_settings_repository.get(db).is_open:
        raise BallotClosedError()
    if entry_repository.get_by_identifier(db, payload.identifier) is not None:
        raise DuplicateEntryError(payload.identifier)
    try:
        return entry_repository.create(db, name=payload.name, identifier=payload.identifier)
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateEntryError(payload.identifier) from exc
