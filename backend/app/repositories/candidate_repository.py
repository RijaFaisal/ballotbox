from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate


def create(
    db: Session, product_id: int, name: str, email: str | None, cnic: str | None
) -> Candidate:
    candidate = Candidate(product_id=product_id, name=name, email=email, cnic=cnic)
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def get_by_product_and_cnic(db: Session, product_id: int, cnic: str) -> Candidate | None:
    return db.execute(
        select(Candidate).where(Candidate.product_id == product_id, Candidate.cnic == cnic)
    ).scalar_one_or_none()


def get_by_product_and_email(db: Session, product_id: int, email: str) -> Candidate | None:
    return db.execute(
        select(Candidate).where(
            Candidate.product_id == product_id, func.lower(Candidate.email) == email.lower()
        )
    ).scalar_one_or_none()


def list_by_product_ordered_by_id(db: Session, product_id: int) -> list[Candidate]:
    return list(
        db.execute(
            select(Candidate).where(Candidate.product_id == product_id).order_by(Candidate.id)
        ).scalars().all()
    )


def count_by_product(db: Session, product_id: int) -> int:
    return db.execute(
        select(func.count()).select_from(Candidate).where(Candidate.product_id == product_id)
    ).scalar_one()


def delete_by_product(db: Session, product_id: int) -> int:
    """Deletes all candidates for one product; returns the count. Caller
    commits. Any winners for this product must already be cleared first --
    winners.candidate_id is ON DELETE RESTRICT."""
    return db.execute(delete(Candidate).where(Candidate.product_id == product_id)).rowcount
