from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.common import get_product_or_404
from app.schemas.candidate import CandidateCreate, CandidateSubmitResult
from app.services.candidate_service import DuplicateCandidateError, submit_candidate

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("", response_model=CandidateSubmitResult, status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidateCreate, db: Session = Depends(get_db)) -> CandidateSubmitResult:
    product = get_product_or_404(db, payload.product_id)

    if not product.is_open:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This product is currently closed. New entries are not being accepted.",
        )

    try:
        candidate = submit_candidate(db, payload)
    except DuplicateCandidateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You're already entered for this product.",
        ) from exc

    return CandidateSubmitResult(name=candidate.name, product_name=product.name)
