from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)

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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductOption(BaseModel):
    """Public, minimal shape for the customer-facing product dropdown --
    deliberately excludes created_at and anything candidate-related."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
