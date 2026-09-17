from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

_CNIC_PATTERN = re.compile(r"^\d{5}-?\d{7}-?\d{1}$")


def normalize_cnic(value: str) -> str:
    """Strips CNIC formatting so "12345-1234567-1" and "1234512345671"
    compare as the same value everywhere (dedup, storage, lookup)."""
    value = value.strip()
    if not _CNIC_PATTERN.match(value):
        raise ValueError("cnic must be 13 digits, e.g. 12345-1234567-1 or 1234512345671")
    return re.sub(r"\D", "", value)


class CandidateCreate(BaseModel):
    product_id: int
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    cnic: str | None = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("cnic")
    @classmethod
    def _normalize_cnic(cls, v: str | None) -> str | None:
        if v is None or v.strip() == "":
            return None
        return normalize_cnic(v)

    @model_validator(mode="after")
    def _require_email_or_cnic(self) -> "CandidateCreate":
        if self.email is None and self.cnic is None:
            raise ValueError("at least one of email or cnic must be provided")
        return self


class CandidateRead(BaseModel):
    """Admin-only view -- includes contact details. Never sent to
    customers, who must never see other candidates."""

    id: int
    name: str
    email: str | None
    cnic: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
