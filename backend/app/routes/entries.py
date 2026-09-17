from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.repositories import entry_repository
from app.schemas.entry import EntryCountRead, EntryCreate, EntryRead
from app.services.entry_service import BallotClosedError, DuplicateEntryError, submit_entry

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("", response_model=EntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(payload: EntryCreate, db: Session = Depends(get_db)) -> EntryRead:
    try:
        entry = submit_entry(db, payload)
    except BallotClosedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The ballot is currently closed. New entries are not being accepted.",
        ) from exc
    except DuplicateEntryError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This identifier has already been entered.",
        ) from exc
    return EntryRead.model_validate(entry)


@router.get("/count", response_model=EntryCountRead)
def get_entry_count(db: Session = Depends(get_db)) -> EntryCountRead:
    return EntryCountRead(count=entry_repository.count_all(db))


@router.get("", response_model=list[EntryRead], dependencies=[Depends(get_current_admin)])
def list_entries(db: Session = Depends(get_db)) -> list[EntryRead]:
    return [
        EntryRead.model_validate(entry)
        for entry in entry_repository.list_all_ordered_by_id(db)
    ]
