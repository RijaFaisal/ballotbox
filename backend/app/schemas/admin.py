from pydantic import BaseModel, Field


class BallotResetRequest(BaseModel):
    confirm: str = Field(min_length=1)


class BallotResetResult(BaseModel):
    entries_deleted: int
    draws_deleted: int
    winners_deleted: int
