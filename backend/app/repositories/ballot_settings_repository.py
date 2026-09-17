from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ballot_settings import BallotSettings

_SINGLETON_ID = 1


def get(db: Session) -> BallotSettings:
    """Returns the single ballot-settings row, creating it (open by
    default) on first access. This way callers never have to special-case
    a missing row, whether the table came from a migration (production)
    or from Base.metadata.create_all() with no seed data (tests).
    """
    settings = db.execute(
        select(BallotSettings).where(BallotSettings.id == _SINGLETON_ID)
    ).scalar_one_or_none()
    if settings is None:
        settings = BallotSettings(id=_SINGLETON_ID, is_open=True)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def set_open(db: Session, is_open: bool) -> BallotSettings:
    settings = get(db)
    settings.is_open = is_open
    db.commit()
    db.refresh(settings)
    return settings
