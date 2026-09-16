from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.results import ResultsRead
from app.services.results_service import get_latest_results

router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=ResultsRead)
def get_results(db: Session = Depends(get_db)) -> ResultsRead:
    return get_latest_results(db)
