import re
from datetime import datetime

from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, ConfigDict, Field, field_validator

_CNIC_PATTERN = re.compile(r"^\d{5}-?\d{7}-?\d{1}$")


def normalize_identifier(value: str) -> str:
    value = value.strip()
    if _CNIC_PATTERN.match(value):
        return re.sub(r"\D", "", value)
    try:
        result = validate_email(value, check_deliverability=False)
    except EmailNotValidError as exc:
        raise ValueError(
            "identifier must be a valid email address or a 13-digit CNIC "
            "(e.g. 12345-1234567-1)"
        ) from exc
    return result.normalized.lower()


class EntryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    identifier: str = Field(min_length=3, max_length=320)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("identifier")
    @classmethod
    def _normalize_identifier(cls, v: str) -> str:
        return normalize_identifier(v)


class EntryRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
