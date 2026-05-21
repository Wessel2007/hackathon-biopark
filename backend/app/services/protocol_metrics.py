"""Métricas e classificação compartilhadas entre relatório PDF e dashboard."""

from datetime import date, datetime
from typing import Optional


def calc_duracao(p: dict) -> Optional[int]:
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


def ultima_consulta(hist: list) -> Optional[dict]:
    if not hist:
        return None
    return max(hist, key=lambda h: h.get("data_consulta") or "")


def classificar_protocolo(p: dict, today: Optional[date] = None) -> str:
    """
    Retorna: mudanca | erro | sem_atualizacao | ok
    Erros têm prioridade sobre mudança (Regra 10).
    """
    today = today or date.today()
    hist = p.get("query_history") or []
    last = ultima_consulta(hist)

    if not last:
        return "sem_atualizacao"

    if last.get("erro"):
        return "erro"

    ultima_str = (last.get("data_consulta") or "")[:10]
    if ultima_str:
        try:
            if (today - date.fromisoformat(ultima_str)).days > 30:
                return "sem_atualizacao"
        except ValueError:
            pass

    if last.get("houve_mudanca"):
        return "mudanca"

    return "ok"


def format_datetime_consulta(value) -> str:
    if not value:
        return "—"
    try:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return str(value)[:16]


def observacao_atual(p: dict) -> str:
    if p.get("observacao_consulta"):
        return str(p["observacao_consulta"])[:200]
    last = ultima_consulta(p.get("query_history") or [])
    if last and last.get("observacao"):
        return str(last["observacao"])[:200]
    return "—"
