from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
from supabase import Client


def _scrape_url(url: str) -> dict:
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        texto = soup.get_text(separator=" ", strip=True)
        return {
            "status_consultado": _extract_status(texto),
            "observacao": texto[:500],
            "texto_bruto": texto[:2000],
            "erro": None,
        }
    except Exception as e:
        return {"status_consultado": None, "observacao": None, "texto_bruto": None, "erro": str(e)}


def _extract_status(texto: str) -> str:
    t = texto.lower()
    if "aprovado" in t or "deferido" in t:
        return "APRO"
    if "indeferido" in t or "reprovado" in t:
        return "REPROVADO"
    if "análise" in t or "andamento" in t:
        return "EM ANDAMENTO"
    if "aguardando" in t:
        return "AGUARDANDO DOCUMENTACAO"
    if "cancelado" in t:
        return "CANCELADO"
    return "PENDENTE"


def _simulate_query(p: dict) -> dict:
    return {
        "status_consultado": p.get("status"),
        "observacao": f"[SIMULADO] Protocolo {p.get('protocolo')} - {p.get('situacao')}",
        "texto_bruto": None,
        "erro": None,
    }


def run_single_query(protocol_id: int, sb: Client) -> dict:
    result = sb.table("protocols").select("*, query_history(*)").eq("id", protocol_id).maybe_single().execute()
    p = result.data
    if not p:
        return {"erro": "Protocolo não encontrado"}

    resultado = _scrape_url(p["url_consulta"]) if p.get("url_consulta") else _simulate_query(p)

    historico = p.get("query_history") or []
    ultimo = historico[-1] if historico else None
    houve_mudanca = bool(ultimo and ultimo.get("status_consultado") != resultado["status_consultado"])

    now = datetime.now(timezone.utc).isoformat()

    sb.table("query_history").insert({
        "protocol_id": protocol_id,
        "status_consultado": resultado["status_consultado"],
        "observacao": resultado["observacao"],
        "texto_bruto": resultado["texto_bruto"],
        "houve_mudanca": houve_mudanca,
        "erro": resultado["erro"],
        "data_consulta": now,
    }).execute()

    update_payload = {"ultima_consulta": now, "observacao_consulta": resultado["observacao"]}
    if resultado["status_consultado"] and not resultado["erro"]:
        update_payload["status"] = resultado["status_consultado"]
    sb.table("protocols").update(update_payload).eq("id", protocol_id).execute()

    return {"protocolo": p["protocolo"], "resultado": resultado, "houve_mudanca": houve_mudanca}


def run_all_queries(sb: Client):
    protocols = sb.table("protocols").select("id").eq("ativo", True).execute().data
    for p in protocols:
        run_single_query(p["id"], sb)
