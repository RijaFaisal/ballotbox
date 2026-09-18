from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminRead(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class AdminAccountCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class AdminDeleteResult(BaseModel):
    deleted: bool = True


class LoginEventRead(BaseModel):
    id: int
    admin_id: int | None
    username: str
    success: bool
    ip_address: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
