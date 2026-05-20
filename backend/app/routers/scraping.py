from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.scraper import run_all_queries, run_single_query
from app.routers.deps import get_current_user

router = APIRouter(prefix="/scraping", tags=["scraping"])


@router.post("/run-all")
def run_all(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    background_tasks.add_task(run_all_queries, db)
    return {"message": "Consulta iniciada em background"}


@router.post("/run/{protocol_id}")
def run_one(
    protocol_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    result = run_single_query(protocol_id, db)
    return result
