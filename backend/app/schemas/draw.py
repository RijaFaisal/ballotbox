from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.draw import DrawStatus


class DrawRead(BaseModel):
    id: int
    product_id: int
    seed: str
    winner_count: int
    status: DrawStatus
    drawn_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class WinnerCandidateRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class WinnerRead(BaseModel):
    position: int
    candidate: WinnerCandidateRead

    model_config = ConfigDict(from_attributes=True)


class DrawDetailRead(DrawRead):
    winners: list[WinnerRead]
