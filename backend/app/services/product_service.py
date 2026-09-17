from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories import candidate_repository, draw_repository, product_repository


@dataclass(frozen=True)
class ProductDeleteCounts:
    candidates_deleted: int
    draws_deleted: int
    winners_deleted: int


@dataclass(frozen=True)
class DrawsClearCounts:
    draws_deleted: int
    winners_deleted: int


@dataclass(frozen=True)
class CandidatesClearCounts:
    candidates_deleted: int
    draws_deleted: int
    winners_deleted: int


def delete_product(db: Session, product: Product) -> ProductDeleteCounts:
    """Deletes a product and everything under it, in the only order that
    respects the foreign keys (same ordering as reset_repository.reset_ballot):
    winners -> draws -> candidates -> product. draws.product_id is ON DELETE
    RESTRICT, so draws must be cleared before the product row goes. Commits
    once so the delete is all-or-nothing.
    """
    draws_deleted, winners_deleted = draw_repository.delete_by_product(db, product.id)
    candidates_deleted = candidate_repository.delete_by_product(db, product.id)
    product_repository.delete(db, product)
    db.commit()
    return ProductDeleteCounts(
        candidates_deleted=candidates_deleted,
        draws_deleted=draws_deleted,
        winners_deleted=winners_deleted,
    )


def clear_draws(db: Session, product_id: int) -> DrawsClearCounts:
    """Clears a product's draw history only -- its candidates are
    untouched, so the same entries can be redrawn from scratch."""
    draws_deleted, winners_deleted = draw_repository.delete_by_product(db, product_id)
    db.commit()
    return DrawsClearCounts(draws_deleted=draws_deleted, winners_deleted=winners_deleted)


def clear_candidates(db: Session, product_id: int) -> CandidatesClearCounts:
    """Clears a product's candidates for a fresh round of entries.

    Draws/winners for this product are cleared first: winners.candidate_id
    is ON DELETE RESTRICT, so a candidate that has won a draw can't be
    deleted while a winner row still points to it.
    """
    draws_deleted, winners_deleted = draw_repository.delete_by_product(db, product_id)
    candidates_deleted = candidate_repository.delete_by_product(db, product_id)
    db.commit()
    return CandidatesClearCounts(
        candidates_deleted=candidates_deleted,
        draws_deleted=draws_deleted,
        winners_deleted=winners_deleted,
    )
