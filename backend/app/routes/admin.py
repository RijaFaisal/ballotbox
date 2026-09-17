from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.schemas.admin import BallotResetRequest, BallotResetResult
from app.services.ballot_reset_service import ResetNotConfirmedError, reset_ballot

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


@router.post("/reset", response_model=BallotResetResult)
def reset_ballot_endpoint(
    payload: BallotResetRequest, db: Session = Depends(get_db)
) -> BallotResetResult:
    try:
        counts = reset_ballot(db, confirm=payload.confirm)
    except ResetNotConfirmedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return BallotResetResult(
        products_deleted=counts.products_deleted,
        candidates_deleted=counts.candidates_deleted,
        draws_deleted=counts.draws_deleted,
        winners_deleted=counts.winners_deleted,
    )
