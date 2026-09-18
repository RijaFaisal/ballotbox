from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories import candidate_repository, draw_repository, product_repository
from app.schemas.product import ProductBulkUploadResult, ProductBulkUploadSkip
from app.services.csv_import import parse_csv_rows


@dataclass(frozen=True)
class DashboardSummary:
    product_count: int
    open_product_count: int
    candidate_count: int


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


def get_dashboard_summary(db: Session) -> DashboardSummary:
    return DashboardSummary(
        product_count=product_repository.count_all(db),
        open_product_count=product_repository.count_open(db),
        candidate_count=candidate_repository.count_all(db),
    )


def set_open(db: Session, product: Product, is_open: bool) -> Product:
    return product_repository.set_open(db, product, is_open)


def set_closes_at(db: Session, product: Product, closes_at: dt.datetime | None) -> Product:
    return product_repository.set_closes_at(db, product, closes_at)


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


def bulk_create_products(db: Session, file_bytes: bytes) -> ProductBulkUploadResult:
    """Creates one product per CSV row (single "name" column).

    Reuses the same case-insensitive uniqueness rule as single product
    creation. A row is skipped (never fails the whole upload) when its
    name is blank, a duplicate of an earlier row in this same file, or
    already exists in the database -- each with its own reported reason.
    """
    rows = parse_csv_rows(file_bytes, required_columns={"name"})

    created_count = 0
    skipped: list[ProductBulkUploadSkip] = []
    seen_names_lower: set[str] = set()

    for row_number, row in enumerate(rows, start=1):
        name = row.get("name", "")

        if not name:
            skipped.append(ProductBulkUploadSkip(row=row_number, name=name, reason="blank name"))
            continue

        name_lower = name.lower()
        if name_lower in seen_names_lower:
            skipped.append(
                ProductBulkUploadSkip(row=row_number, name=name, reason="duplicate in file")
            )
            continue

        if product_repository.get_by_name(db, name) is not None:
            skipped.append(
                ProductBulkUploadSkip(row=row_number, name=name, reason="already exists")
            )
            continue

        try:
            product_repository.create(db, name=name)
        except IntegrityError:
            db.rollback()
            skipped.append(
                ProductBulkUploadSkip(row=row_number, name=name, reason="already exists")
            )
            continue

        created_count += 1
        seen_names_lower.add(name_lower)

    return ProductBulkUploadResult(created_count=created_count, skipped=skipped)
