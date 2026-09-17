from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.repositories import candidate_repository
from app.schemas.candidate import CandidateCreate


class DuplicateCandidateError(Exception):
    """Raised when this person has already entered this product.

    Dedup rule: match on CNIC if the submission provided one, else match
    on email -- never both, since either field alone is enough to identify
    a returning person for a given product.
    """


def submit_candidate(db: Session, payload: CandidateCreate) -> Candidate:
    if payload.cnic is not None:
        existing = candidate_repository.get_by_product_and_cnic(
            db, payload.product_id, payload.cnic
        )
    else:
        existing = candidate_repository.get_by_product_and_email(
            db, payload.product_id, payload.email
        )

    if existing is not None:
        raise DuplicateCandidateError()

    try:
        return candidate_repository.create(
            db,
            product_id=payload.product_id,
            name=payload.name,
            email=payload.email,
            cnic=payload.cnic,
        )
    except IntegrityError as exc:
        # Safety net for a race between two concurrent submissions that both
        # passed the pre-check above -- the partial unique indexes catch it.
        db.rollback()
        raise DuplicateCandidateError() from exc
