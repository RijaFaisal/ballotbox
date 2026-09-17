from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.results import DrawHistoryDetail, DrawHistoryEntry, ResultsRead
from app.services.results_service import (
    get_draw_history,
    get_history_detail,
    get_history_entry,
    get_latest_results,
)

router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=ResultsRead)
def get_results(db: Session = Depends(get_db)) -> ResultsRead:
    return get_latest_results(db)


@router.get("/history", response_model=list[DrawHistoryEntry])
def list_results_history(db: Session = Depends(get_db)) -> list[DrawHistoryEntry]:
    return [get_history_entry(draw) for draw in get_draw_history(db)]


@router.get("/history/{draw_id}", response_model=DrawHistoryDetail)
def get_results_history_detail(draw_id: int, db: Session = Depends(get_db)) -> DrawHistoryDetail:
    detail = get_history_detail(db, draw_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draw not found.")
    return detail
