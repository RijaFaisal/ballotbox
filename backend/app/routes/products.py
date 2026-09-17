from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.models.product import Product
from app.repositories import candidate_repository, product_repository
from app.schemas.candidate import CandidateRead
from app.schemas.product import ProductCreate, ProductRead

# No router-level auth dependency: product creation and the candidate list
# are admin-only, but a future public "list products for the entry form
# dropdown" route belongs on this same router without exposing candidates.
router = APIRouter(prefix="/products", tags=["products"])


def _get_product_or_404(db: Session, product_id: int) -> Product:
    product = product_repository.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> ProductRead:
    if product_repository.get_by_name(db, payload.name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this name already exists.",
        )
    try:
        product = product_repository.create(db, name=payload.name)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A product with this name already exists.",
        ) from exc
    return ProductRead.model_validate(product)


@router.get("", response_model=list[ProductRead], dependencies=[Depends(get_current_admin)])
def list_products(db: Session = Depends(get_db)) -> list[ProductRead]:
    return [
        ProductRead.model_validate(product)
        for product in product_repository.list_all_ordered_by_created_at(db)
    ]


@router.get(
    "/{product_id}/candidates",
    response_model=list[CandidateRead],
    dependencies=[Depends(get_current_admin)],
)
def list_candidates_for_product(
    product_id: int, db: Session = Depends(get_db)
) -> list[CandidateRead]:
    _get_product_or_404(db, product_id)
    return [
        CandidateRead.model_validate(candidate)
        for candidate in candidate_repository.list_by_product_ordered_by_id(db, product_id)
    ]
