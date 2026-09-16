from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.entry import EntryCreate, EntryRead
from app.services.entry_service import DuplicateEntryError, submit_entry

router = APIRouter(prefix="/entries", tags=["entries"])


@router.post("", response_model=EntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(payload: EntryCreate, db: Session = Depends(get_db)) -> EntryRead:
    try:
        entry = submit_entry(db, payload)
    except DuplicateEntryError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This identifier has already been entered.",
        ) from exc
    return EntryRead.model_validate(entry)
