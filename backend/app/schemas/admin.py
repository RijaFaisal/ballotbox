from pydantic import BaseModel, Field


class BallotResetRequest(BaseModel):
    confirm: str = Field(min_length=1)


class BallotResetResult(BaseModel):
    products_deleted: int
    candidates_deleted: int
    draws_deleted: int
    winners_deleted: int
