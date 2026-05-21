from datetime import date
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from supabase import Client
import io

from app.supabase_client import get_supabase
from app.services.report import generate_pdf_report
from app.routers.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/pdf")
def get_pdf_report(sb: Client = Depends(get_supabase), _: str = Depends(get_current_user)):
    pdf_bytes = generate_pdf_report(sb)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio_protocolos.pdf"},
    )


@router.get("/dashboard-data")
def get_dashboard_data(sb: Client = Depends(get_supabase), _: str = Depends(get_current_user)):
    protocols = sb.table("protocols").select("*, query_history(*)").execute().data

    total = len(protocols)
    ativos = sum(1 for p in protocols if p.get("ativo"))
    com_mudanca = sum(
        1 for p in protocols
        if p.get("query_history") and p["query_history"][-1].get("houve_mudanca")
    )

    por_projeto: dict = {}
    for p in protocols:
        abertura = p.get("data_abertura")
        fim = p.get("data_finalizacao")
        if abertura:
            d_abertura = date.fromisoformat(abertura)
            d_fim = date.fromisoformat(fim) if fim else date.today()
            duracao = (d_fim - d_abertura).days
        else:
            duracao = None

        historico = p.get("query_history") or []
        por_projeto.setdefault(p["projeto"], []).append({
            "id": p["id"],
            "protocolo": p["protocolo"],
            "status": p["status"],
            "situacao": p.get("situacao"),
            "ativo": p.get("ativo"),
            "ultima_consulta": p.get("ultima_consulta"),
            "houve_mudanca": bool(historico and historico[-1].get("houve_mudanca")),
            "duracao_dias": duracao,
        })

    return {"total": total, "ativos": ativos, "com_mudanca_recente": com_mudanca, "por_projeto": por_projeto}
