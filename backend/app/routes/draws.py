from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.repositories import draw_repository
from app.schemas.draw import DrawCreate, DrawDetailRead, DrawRead
from app.services.draw_service import DrawAlreadyCompletedError, NotEnoughEntriesError, run_draw

router = APIRouter(prefix="/draws", tags=["draws"], dependencies=[Depends(get_current_admin)])


@router.post("", response_model=DrawDetailRead, status_code=status.HTTP_201_CREATED)
def create_draw(payload: DrawCreate, db: Session = Depends(get_db)) -> DrawDetailRead:
    try:
        draw = run_draw(db, winner_count=payload.winner_count)
    except NotEnoughEntriesError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except DrawAlreadyCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return DrawDetailRead.model_validate(draw)


@router.get("", response_model=list[DrawRead])
def list_draws(db: Session = Depends(get_db)) -> list[DrawRead]:
    return [DrawRead.model_validate(draw) for draw in draw_repository.list_all(db)]


@router.get("/{draw_id}", response_model=DrawDetailRead)
def get_draw(draw_id: int, db: Session = Depends(get_db)) -> DrawDetailRead:
    draw = draw_repository.get_by_id(db, draw_id)
    if draw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draw not found.")
    return DrawDetailRead.model_validate(draw)
