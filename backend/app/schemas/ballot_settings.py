from pydantic import BaseModel


class BallotStatusRead(BaseModel):
    is_open: bool
