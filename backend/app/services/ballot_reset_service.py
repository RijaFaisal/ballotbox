from sqlalchemy.orm import Session

from app.repositories import reset_repository
from app.repositories.reset_repository import ResetCounts

# Deliberately not configurable and not exposed as a query param: an admin
# must know and type this exact phrase for the reset to run at all, so a
# stray/automated/scripted POST to this endpoint can't wipe data by accident.
CONFIRMATION_PHRASE = "RESET"


class ResetNotConfirmedError(Exception):
    pass


def reset_ballot(db: Session, confirm: str) -> ResetCounts:
    if confirm != CONFIRMATION_PHRASE:
        raise ResetNotConfirmedError(
            f'Type "{CONFIRMATION_PHRASE}" exactly (case-sensitive) to confirm the reset.'
        )
    return reset_repository.reset_ballot(db)
