from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.repositories import candidate_repository, product_repository
from app.routes.common import get_product_or_404
from app.schemas.candidate import CandidateRead
from app.schemas.product import (
    ProductCandidatesClearResult,
    ProductCreate,
    ProductDeleteResult,
    ProductOption,
    ProductRead,
)
from app.services import product_service

# No router-level auth dependency: product creation and the candidate list
# are admin-only, but /products/public (the entry form's dropdown) is not.
router = APIRouter(prefix="/products", tags=["products"])


@router.get("/public", response_model=list[ProductOption])
def list_products_public(db: Session = Depends(get_db)) -> list[ProductOption]:
    return [
        ProductOption.model_validate(product)
        for product in product_repository.list_all_ordered_by_name(db)
    ]


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
    get_product_or_404(db, product_id)
    return [
        CandidateRead.model_validate(candidate)
        for candidate in candidate_repository.list_by_product_ordered_by_id(db, product_id)
    ]


@router.delete(
    "/{product_id}",
    response_model=ProductDeleteResult,
    dependencies=[Depends(get_current_admin)],
)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> ProductDeleteResult:
    product = get_product_or_404(db, product_id)
    counts = product_service.delete_product(db, product)
    return ProductDeleteResult(
        candidates_deleted=counts.candidates_deleted,
        draws_deleted=counts.draws_deleted,
        winners_deleted=counts.winners_deleted,
    )


@router.delete(
    "/{product_id}/candidates",
    response_model=ProductCandidatesClearResult,
    dependencies=[Depends(get_current_admin)],
)
def clear_product_candidates(
    product_id: int, db: Session = Depends(get_db)
) -> ProductCandidatesClearResult:
    get_product_or_404(db, product_id)
    counts = product_service.clear_candidates(db, product_id)
    return ProductCandidatesClearResult(
        candidates_deleted=counts.candidates_deleted,
        draws_deleted=counts.draws_deleted,
        winners_deleted=counts.winners_deleted,
    )
