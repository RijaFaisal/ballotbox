from sqlalchemy.orm import Session

from app.models.ballot_settings import BallotSettings
from app.repositories import ballot_settings_repository


def get_status(db: Session) -> BallotSettings:
    return ballot_settings_repository.get(db)


def toggle_status(db: Session) -> BallotSettings:
    current = ballot_settings_repository.get(db)
    return ballot_settings_repository.set_open(db, not current.is_open)
