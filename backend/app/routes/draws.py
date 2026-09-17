from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.repositories import draw_repository
from app.routes.common import get_product_or_404
from app.schemas.draw import DrawDetailRead, DrawsClearResult
from app.services import draw_export_service, product_service
from app.services.draw_service import NotEnoughEntriesError, run_draw

# Each product's draw is independent: winning one product never excludes a
# candidate from another, and every draw here always selects exactly one
# winner from that product's own candidates.
router = APIRouter(
    prefix="/products/{product_id}/draws",
    tags=["draws"],
    dependencies=[Depends(get_current_admin)],
)

_WINNER_COUNT = 1


@router.post("", response_model=DrawDetailRead, status_code=status.HTTP_201_CREATED)
def create_draw(product_id: int, db: Session = Depends(get_db)) -> DrawDetailRead:
    get_product_or_404(db, product_id)
    try:
        draw = run_draw(db, product_id=product_id, winner_count=_WINNER_COUNT)
    except NotEnoughEntriesError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return DrawDetailRead.model_validate(draw)


@router.get("", response_model=list[DrawDetailRead])
def list_draws(product_id: int, db: Session = Depends(get_db)) -> list[DrawDetailRead]:
    get_product_or_404(db, product_id)
    return [
        DrawDetailRead.model_validate(draw)
        for draw in draw_repository.list_by_product(db, product_id)
    ]


@router.delete("", response_model=DrawsClearResult)
def clear_draws(product_id: int, db: Session = Depends(get_db)) -> DrawsClearResult:
    get_product_or_404(db, product_id)
    counts = product_service.clear_draws(db, product_id)
    return DrawsClearResult(draws_deleted=counts.draws_deleted, winners_deleted=counts.winners_deleted)


def _get_draw_for_product_or_404(db: Session, product_id: int, draw_id: int):
    draw = draw_repository.get_by_id(db, draw_id)
    if draw is None or draw.product_id != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draw not found.")
    return draw


@router.get("/{draw_id}", response_model=DrawDetailRead)
def get_draw(product_id: int, draw_id: int, db: Session = Depends(get_db)) -> DrawDetailRead:
    draw = _get_draw_for_product_or_404(db, product_id, draw_id)
    return DrawDetailRead.model_validate(draw)


def _safe_filename_slug(name: str) -> str:
    # The product name is admin-entered free text; strip it down to a safe
    # ASCII slug before it lands in a Content-Disposition header, so a name
    # with quotes/newlines/unicode can't break or inject into the header.
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-")
    return slug or "product"


@router.get("/{draw_id}/export")
def export_draw_winner_pdf(product_id: int, draw_id: int, db: Session = Depends(get_db)) -> Response:
    product = get_product_or_404(db, product_id)
    draw = _get_draw_for_product_or_404(db, product_id, draw_id)
    pdf_bytes = draw_export_service.winners_pdf(db, draw, product)
    filename = f"{_safe_filename_slug(product.name)}-draw-{draw_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
