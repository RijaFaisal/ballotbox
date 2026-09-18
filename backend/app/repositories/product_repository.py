from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.product import Product


def create(db: Session, name: str, closes_at: dt.datetime | None = None) -> Product:
    product = Product(name=name, closes_at=closes_at)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def _effectively_open_clause():
    # Mirrors Product.effectively_open in SQL: is_open AND (no deadline, or
    # the deadline hasn't passed yet). A bound Python "now" is used rather
    # than func.now() so this filters identically on SQLite (tests) and
    # Postgres (production).
    now = dt.datetime.now(dt.timezone.utc)
    return Product.is_open.is_(True) & (Product.closes_at.is_(None) | (Product.closes_at > now))


def get_by_id(db: Session, product_id: int) -> Product | None:
    return db.execute(select(Product).where(Product.id == product_id)).scalar_one_or_none()


def get_by_name(db: Session, name: str) -> Product | None:
    return db.execute(
        select(Product).where(func.lower(Product.name) == name.lower())
    ).scalar_one_or_none()


def list_all_ordered_by_created_at(db: Session) -> list[Product]:
    return list(
        db.execute(
            select(Product).order_by(Product.created_at.desc(), Product.id.desc())
        ).scalars().all()
    )


def list_open_ordered_by_name(db: Session) -> list[Product]:
    """Alphabetical, effectively-open products only -- this is the
    customer-facing dropdown, where "newest first" has no obvious value and
    a closed (manually or by a passed schedule) product shouldn't be
    offered at all."""
    return list(
        db.execute(
            select(Product).where(_effectively_open_clause()).order_by(func.lower(Product.name))
        ).scalars().all()
    )


def delete(db: Session, product: Product) -> None:
    db.delete(product)


def set_open(db: Session, product: Product, is_open: bool) -> Product:
    product.is_open = is_open
    db.commit()
    db.refresh(product)
    return product


def set_closes_at(db: Session, product: Product, closes_at: dt.datetime | None) -> Product:
    product.closes_at = closes_at
    db.commit()
    db.refresh(product)
    return product


def count_all(db: Session) -> int:
    return db.execute(select(func.count()).select_from(Product)).scalar_one()


def count_open(db: Session) -> int:
    return db.execute(
        select(func.count()).select_from(Product).where(_effectively_open_clause())
    ).scalar_one()
