from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    closes_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v


class ProductRead(BaseModel):
    id: int
    name: str
    is_open: bool
    closes_at: datetime | None
    # Computed from is_open + closes_at (see Product.effectively_open) --
    # the actual state entrants see, distinct from the raw is_open switch.
    effectively_open: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductClosesAtUpdate(BaseModel):
    closes_at: datetime | None


class ProductOption(BaseModel):
    """Public, minimal shape for the customer-facing product dropdown --
    deliberately excludes created_at and anything candidate-related."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ProductOpenUpdate(BaseModel):
    is_open: bool


class ProductDeleteResult(BaseModel):
    candidates_deleted: int
    draws_deleted: int
    winners_deleted: int


class ProductCandidatesClearResult(BaseModel):
    candidates_deleted: int
    draws_deleted: int
    winners_deleted: int


class ProductBulkUploadSkip(BaseModel):
    row: int
    name: str
    reason: str


class ProductBulkUploadResult(BaseModel):
    created_count: int
    skipped: list[ProductBulkUploadSkip]


class DashboardSummary(BaseModel):
    product_count: int
    open_product_count: int
    candidate_count: int
