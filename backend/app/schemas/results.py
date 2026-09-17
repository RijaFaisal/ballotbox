from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ResultsWinner(BaseModel):
    position: int
    name: str


class ResultsRead(BaseModel):
    has_results: bool
    drawn_at: datetime | None = None
    winners: list[ResultsWinner] = []


class DrawHistoryEntry(BaseModel):
    id: int
    drawn_at: datetime
    winner_count: int


class DrawHistoryDetail(DrawHistoryEntry):
    winners: list[ResultsWinner]
