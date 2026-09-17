from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.schemas.ballot_settings import BallotStatusRead
from app.services.ballot_settings_service import get_status, toggle_status

router = APIRouter(prefix="/ballot", tags=["ballot"])


@router.get("/status", response_model=BallotStatusRead)
def get_ballot_status(db: Session = Depends(get_db)) -> BallotStatusRead:
    return BallotStatusRead(is_open=get_status(db).is_open)


@router.post(
    "/toggle", response_model=BallotStatusRead, dependencies=[Depends(get_current_admin)]
)
def toggle_ballot_status(db: Session = Depends(get_db)) -> BallotStatusRead:
    return BallotStatusRead(is_open=toggle_status(db).is_open)
