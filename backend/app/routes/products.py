from __future__ import annotations

import re

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.database import get_db
from app.repositories import candidate_repository, product_repository
from app.routes.common import get_product_or_404
from app.schemas.candidate import CandidateRead
from app.schemas.product import (
    DashboardSummary,
    ProductBulkUploadResult,
    ProductCandidatesClearResult,
    ProductCreate,
    ProductDeleteResult,
    ProductOpenUpdate,
    ProductOption,
    ProductRead,
)
from app.services import candidate_export_service, product_service
from app.services.csv_import import CsvFormatError

# No router-level auth dependency: product creation and the candidate list
# are admin-only, but /products/public (the entry form's dropdown) is not.
router = APIRouter(prefix="/products", tags=["products"])


def _safe_filename_slug(name: str) -> str:
    # Same treatment as the PDF export's filename: an admin-entered product
    # name is free text, so strip it to a safe ASCII slug before it lands
    # in a Content-Disposition header.
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-")
    return slug or "product"


@router.get("/public", response_model=list[ProductOption])
def list_products_public(db: Session = Depends(get_db)) -> list[ProductOption]:
    return [
        ProductOption.model_validate(product)
        for product in product_repository.list_open_ordered_by_name(db)
    ]


@router.get(
    "/summary",
    response_model=DashboardSummary,
    dependencies=[Depends(get_current_admin)],
)
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    summary = product_service.get_dashboard_summary(db)
    return DashboardSummary(
        product_count=summary.product_count,
        open_product_count=summary.open_product_count,
        candidate_count=summary.candidate_count,
    )


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


@router.post(
    "/bulk-upload",
    response_model=ProductBulkUploadResult,
    dependencies=[Depends(get_current_admin)],
)
async def bulk_upload_products(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> ProductBulkUploadResult:
    file_bytes = await file.read()
    try:
        return product_service.bulk_create_products(db, file_bytes)
    except CsvFormatError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("", response_model=list[ProductRead], dependencies=[Depends(get_current_admin)])
def list_products(db: Session = Depends(get_db)) -> list[ProductRead]:
    return [
        ProductRead.model_validate(product)
        for product in product_repository.list_all_ordered_by_created_at(db)
    ]


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(get_current_admin)],
)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    product = get_product_or_404(db, product_id)
    return ProductRead.model_validate(product)


@router.post(
    "/{product_id}/open",
    response_model=ProductRead,
    dependencies=[Depends(get_current_admin)],
)
def set_product_open(
    product_id: int, payload: ProductOpenUpdate, db: Session = Depends(get_db)
) -> ProductRead:
    product = get_product_or_404(db, product_id)
    updated = product_service.set_open(db, product, payload.is_open)
    return ProductRead.model_validate(updated)


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


@router.get(
    "/{product_id}/candidates/export",
    dependencies=[Depends(get_current_admin)],
)
def export_candidates_csv(product_id: int, db: Session = Depends(get_db)) -> Response:
    product = get_product_or_404(db, product_id)
    csv_text = candidate_export_service.candidates_csv(db, product_id)
    filename = f"{_safe_filename_slug(product.name)}-candidates.csv"
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
