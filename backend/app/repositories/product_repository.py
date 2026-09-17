from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.product import Product


def create(db: Session, name: str) -> Product:
    product = Product(name=name)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


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
