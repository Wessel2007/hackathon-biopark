from datetime import date, timedelta
from collections import Counter
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import io

from app.supabase_client import SupabaseClient, get_supabase
from app.services.report import generate_pdf_report
from app.routers.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


_NAN_STRINGS = {"nan", "none", "nat", "n/a", ""}


def _clean_str(v) -> str:
    if not v:
        return "—"
    s = str(v).strip()
    return "—" if s.lower() in _NAN_STRINGS else s


def _calc_duracao(p: dict) -> int | None:
    abertura = p.get("data_abertura")
    fim = p.get("data_finalizacao")
    try:
        if not abertura:
            return None
        d0 = date.fromisoformat(str(abertura))
        d1 = date.fromisoformat(str(fim)) if fim else date.today()
        return max(0, (d1 - d0).days)
    except (ValueError, TypeError):
        return None


def _apply_filters(q, projeto, orgao, status, ativo, atribuido_a, situacao, data_abertura_inicio, data_abertura_fim):
    if projeto:
        q = q.ilike("projeto", f"%{projeto}%")
    if orgao:
        q = q.ilike("orgao_site_consultado", f"%{orgao}%")
    if status:
        q = q.eq("status", status)
    if ativo is not None:
        q = q.eq("ativo", ativo)
    if atribuido_a:
        q = q.ilike("atribuido_a", f"%{atribuido_a}%")
    if situacao:
        q = q.ilike("situacao", f"%{situacao}%")
    if data_abertura_inicio:
        q = q.gte("data_abertura", str(data_abertura_inicio))
    if data_abertura_fim:
        q = q.lte("data_abertura", str(data_abertura_fim))
    return q


@router.get("/pdf")
def get_pdf_report(
    projeto: Optional[str] = Query(default=None),
    orgao: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    ativo: Optional[bool] = Query(default=None),
    atribuido_a: Optional[str] = Query(default=None),
    situacao: Optional[str] = Query(default=None),
    data_abertura_inicio: Optional[date] = Query(default=None),
    data_abertura_fim: Optional[date] = Query(default=None),
    sb: SupabaseClient = Depends(get_supabase),
    _: str = Depends(get_current_user),
):
    filters = {
        "projeto": projeto,
        "orgao": orgao,
        "status": status,
        "ativo": ativo,
        "atribuido_a": atribuido_a,
        "situacao": situacao,
        "data_abertura_inicio": data_abertura_inicio,
        "data_abertura_fim": data_abertura_fim,
    }
    pdf_bytes = generate_pdf_report(sb, filters)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio_protocolos.pdf"},
    )


@router.get("/dashboard-data")
def get_dashboard_data(
    projeto: Optional[str] = Query(default=None),
    orgao: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    ativo: Optional[bool] = Query(default=None),
    atribuido_a: Optional[str] = Query(default=None),
    situacao: Optional[str] = Query(default=None),
    data_abertura_inicio: Optional[date] = Query(default=None),
    data_abertura_fim: Optional[date] = Query(default=None),
    sb: SupabaseClient = Depends(get_supabase),
    _: str = Depends(get_current_user),
):
    q = sb.table("protocols").select("*, query_history(*)")
    q = _apply_filters(q, projeto, orgao, status, ativo, atribuido_a, situacao, data_abertura_inicio, data_abertura_fim)
    protocols = q.execute().data

    today = date.today()
    protocols_dur = [(p, _calc_duracao(p)) for p in protocols]

    # KPIs
    total = len(protocols)
    ativos_count = sum(1 for p in protocols if p.get("ativo"))
    com_mudanca = sum(
        1 for p in protocols
        if p.get("query_history") and p["query_history"][-1].get("houve_mudanca")
    )
    erros_consulta = sum(
        1 for p in protocols
        if p.get("query_history") and p["query_history"][-1].get("erro")
    )

    duracoes = [dur for _, dur in protocols_dur if dur is not None]
    duracao_media = round(sum(duracoes) / len(duracoes), 1) if duracoes else 0

    orgaos_list = [_clean_str(p.get("orgao_site_consultado")) for p in protocols]
    orgao_counter = Counter(orgaos_list)
    orgao_top = orgao_counter.most_common(1)[0][0] if orgao_counter else "—"

    # Por status (pie chart)
    status_counter = Counter(p.get("status") or "—" for p in protocols)
    por_status = [{"status": s, "count": c} for s, c in status_counter.items()]

    # Por órgão (bar chart, top 8)
    por_orgao = [{"orgao": o, "count": c} for o, c in orgao_counter.most_common(8)]

    # Por atribuído (bar chart)
    atribuido_counter = Counter(_clean_str(p.get("atribuido_a")) for p in protocols)
    por_atribuido = [{"atribuido_a": a, "count": c} for a, c in atribuido_counter.most_common(8)]

    # Consultas por período (area chart, last 30 days)
    periodo: dict = {
        (today - timedelta(days=i)).isoformat(): 0
        for i in range(29, -1, -1)
    }
    for p in protocols:
        for h in p.get("query_history") or []:
            data_str = (h.get("data_consulta") or "")[:10]
            if data_str in periodo:
                periodo[data_str] += 1
    consultas_por_periodo = [{"data": d, "count": c} for d, c in periodo.items()]

    # Protocolos críticos
    protocolos_criticos = []
    for p, dur in protocols_dur:
        hist = p.get("query_history") or []
        last = hist[-1] if hist else None

        if last and last.get("erro"):
            tipo = "erro"
        elif not hist:
            tipo = "sem_atualizacao"
        elif last:
            ultima_str = (last.get("data_consulta") or "")[:10]
            if ultima_str and (today - date.fromisoformat(ultima_str)).days > 30:
                tipo = "sem_atualizacao"
            elif dur and dur > 180:
                tipo = "duracao_alta"
            else:
                continue
        else:
            continue

        protocolos_criticos.append({
            "id": p["id"],
            "protocolo": p["protocolo"],
            "projeto": p["projeto"],
            "orgao": _clean_str(p.get("orgao_site_consultado")),
            "status": p["status"],
            "tipo": tipo,
            "duracao_dias": dur,
            "ultima_consulta": p.get("ultima_consulta"),
        })

    # Alertas recentes
    alertas: list = []
    for p in protocols:
        for h in p.get("query_history") or []:
            if h.get("houve_mudanca") or h.get("erro"):
                alertas.append({
                    "protocolo": p["protocolo"],
                    "projeto": p["projeto"],
                    "tipo": "erro" if h.get("erro") else "mudanca",
                    "descricao": h.get("erro") or "Mudança de status detectada",
                    "data": h.get("data_consulta") or "",
                })
    alertas.sort(key=lambda x: x["data"], reverse=True)
    alertas_recentes = alertas[:15]

    # Por projeto
    por_projeto: dict = {}
    for p, dur in protocols_dur:
        hist = p.get("query_history") or []
        por_projeto.setdefault(p["projeto"], []).append({
            "id": p["id"],
            "protocolo": p["protocolo"],
            "status": p["status"],
            "situacao": p.get("situacao"),
            "ativo": p.get("ativo"),
            "ultima_consulta": p.get("ultima_consulta"),
            "houve_mudanca": bool(hist and hist[-1].get("houve_mudanca")),
            "duracao_dias": dur,
        })

    return {
        "kpis": {
            "total": total,
            "ativos": ativos_count,
            "com_mudanca_recente": com_mudanca,
            "erros_consulta": erros_consulta,
            "duracao_media": duracao_media,
            "orgao_top": orgao_top,
        },
        "por_status": por_status,
        "por_orgao": por_orgao,
        "por_atribuido": por_atribuido,
        "consultas_por_periodo": consultas_por_periodo,
        "protocolos_criticos": protocolos_criticos[:20],
        "alertas_recentes": alertas_recentes,
        "por_projeto": por_projeto,
        "total": total,
        "ativos": ativos_count,
        "com_mudanca_recente": com_mudanca,
    }
