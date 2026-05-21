import base64

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from fastapi.responses import Response

from app.supabase_client import SupabaseClient, get_supabase
from app.services.scraper import run_all_queries, run_single_query
from app.routers.deps import get_current_user

router = APIRouter(prefix="/scraping", tags=["scraping"])


@router.post("/run-all")
def run_all(
    background_tasks: BackgroundTasks,
    sb: SupabaseClient = Depends(get_supabase),
    current_user: str = Depends(get_current_user),
):
    background_tasks.add_task(run_all_queries, sb, current_user)
    return {"message": "Consulta iniciada em background"}


@router.post("/run/{protocol_id}")
def run_one(
    protocol_id: int,
    sb: SupabaseClient = Depends(get_supabase),
    current_user: str = Depends(get_current_user),
):
    return run_single_query(protocol_id, sb, current_user)


@router.get("/evidence/{history_id}")
def get_evidence(
    history_id: int,
    sb: SupabaseClient = Depends(get_supabase),
    current_user: str = Depends(get_current_user),
):
    """Retorna o screenshot (PNG) capturado durante a consulta como evidência."""
    row = (
        sb.table("query_history")
        .select("screenshot_base64, data_consulta, fonte_consulta")
        .eq("id", history_id)
        .maybe_single()
        .execute()
        .data
    )
    if not row:
        raise HTTPException(status_code=404, detail="Registro de consulta não encontrado.")
    if not row.get("screenshot_base64"):
        raise HTTPException(status_code=404, detail="Evidência não disponível para esta consulta.")

    img_bytes = base64.b64decode(row["screenshot_base64"])
    return Response(
        content=img_bytes,
        media_type="image/png",
        headers={
            "Content-Disposition": f'inline; filename="evidencia_{history_id}.png"',
        },
    )
