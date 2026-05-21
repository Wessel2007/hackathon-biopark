from fastapi import APIRouter, Depends, BackgroundTasks
from supabase import Client

from app.supabase_client import get_supabase
from app.services.scraper import run_all_queries, run_single_query
from app.routers.deps import get_current_user

router = APIRouter(prefix="/scraping", tags=["scraping"])


@router.post("/run-all")
def run_all(
    background_tasks: BackgroundTasks,
    sb: Client = Depends(get_supabase),
    _: str = Depends(get_current_user),
):
    background_tasks.add_task(run_all_queries, sb)
    return {"message": "Consulta iniciada em background"}


@router.post("/run/{protocol_id}")
def run_one(
    protocol_id: int,
    sb: Client = Depends(get_supabase),
    _: str = Depends(get_current_user),
):
    return run_single_query(protocol_id, sb)
