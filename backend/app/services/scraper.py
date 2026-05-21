from datetime import datetime, timezone
import re
import json
import httpx
from bs4 import BeautifulSoup

from app.supabase_client import SupabaseClient


def _scrape_url(url: str) -> dict:
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        texto = soup.get_text(separator=" ", strip=True)
        nao_encontrado = _detect_not_found(texto)
        return {
            "status_consultado": None if nao_encontrado else _extract_status(texto),
            "situacao_consultada": "NAO_ENCONTRADO" if nao_encontrado else None,
            "observacao": texto[:500],
            "texto_bruto": texto[:2000],
            "data_movimentacao": _extract_data_movimentacao(texto),
            "erro": None,
        }
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException):
        return {
            "status_consultado": None, "situacao_consultada": None,
            "observacao": None, "texto_bruto": None,
            "data_movimentacao": None, "erro": "Site indisponível",
        }
    except Exception as e:
        return {
            "status_consultado": None, "situacao_consultada": None,
            "observacao": None, "texto_bruto": None,
            "data_movimentacao": None, "erro": str(e)[:200],
        }


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


def _extract_data_movimentacao(texto: str) -> str | None:
    """Extract the most recent movement/update date (dd/mm/yyyy) from page text."""
    patterns = [
        r'data\s+(?:de\s+)?(?:movimenta[çc][aã]o|atualiza[çc][aã]o|despacho|entrada)\s*:?\s*(\d{2}/\d{2}/\d{4})',
        r'(?:última\s+)?movimenta[çc][aã]o\s+(?:em\s+)?:?\s*(\d{2}/\d{2}/\d{4})',
        r'(?:atualizado|despachado|entrada)\s+(?:em\s+)?:?\s*(\d{2}/\d{2}/\d{4})',
        r'(\d{2}/\d{2}/\d{4})\s*[-–]\s*(?:movimenta[çc][aã]o|despacho)',
    ]
    for pattern in patterns:
        m = re.search(pattern, texto, re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def _detect_not_found(texto: str) -> bool:
    """Return True if the page indicates the protocol was not found."""
    keywords = [
        "não encontrado", "nao encontrado", "não localizado", "nao localizado",
        "não foi encontrado", "registro não encontrado", "protocolo não localizado",
        "sem resultados", "nenhum resultado encontrado",
    ]
    t = texto.lower()
    return any(kw in t for kw in keywords)


def _build_mudancas(ultimo: dict | None, resultado: dict, protocolo_num: str) -> list[str]:
    """Compare current query result against the last history entry.
    Returns human-readable descriptions of every detected change."""
    mudancas = []
    num = protocolo_num

    # 1. Site unavailable
    if resultado.get("erro"):
        erro_anterior = ultimo.get("erro") if ultimo else None
        if not erro_anterior:
            mudancas.append(f"Protocolo {num}: site ficou indisponível")
        return mudancas

    # If previous query had error and now site is back
    if ultimo and ultimo.get("erro"):
        mudancas.append(f"Protocolo {num}: site voltou a responder")

    # 2. Protocol no longer found
    not_found_now = resultado.get("situacao_consultada") == "NAO_ENCONTRADO"
    not_found_before = (ultimo or {}).get("situacao_consultada") == "NAO_ENCONTRADO"
    if not_found_now and not not_found_before:
        mudancas.append(f"Protocolo {num} deixou de ser encontrado no site")
        return mudancas
    if not_found_now:
        return mudancas  # Still not found, no new change

    # No previous history — first query, nothing to compare
    if not ultimo:
        return mudancas

    # 3. Status changed
    status_ant = ultimo.get("status_consultado")
    status_nov = resultado.get("status_consultado")
    if status_ant and status_nov and status_ant != status_nov:
        mudancas.append(f'Protocolo {num} mudou de "{status_ant}" para "{status_nov}"')

    # 4. Observation changed (new text or updated text)
    obs_ant = (ultimo.get("observacao") or "").strip()
    obs_nov = (resultado.get("observacao") or "").strip()
    if obs_nov and not obs_ant:
        mudancas.append(f"Protocolo {num}: nova observação registrada")
    elif obs_nov and obs_ant and obs_nov != obs_ant:
        mudancas.append(f"Protocolo {num}: observação foi atualizada")

    # 5. Movement date changed
    data_ant = (ultimo.get("data_movimentacao") or "").strip()
    data_nov = (resultado.get("data_movimentacao") or "").strip()
    if data_nov and not data_ant:
        mudancas.append(f"Protocolo {num}: nova data de movimentação registrada ({data_nov})")
    elif data_nov and data_ant and data_nov != data_ant:
        mudancas.append(f"Protocolo {num}: data de movimentação mudou de {data_ant} para {data_nov}")

    return mudancas


def _simulate_query(p: dict) -> dict:
    return {
        "status_consultado": p.get("status"),
        "situacao_consultada": None,
        "observacao": f"[SIMULADO] Protocolo {p.get('protocolo')} - {p.get('situacao')}",
        "texto_bruto": None,
        "data_movimentacao": None,
        "erro": None,
    }


def run_single_query(protocol_id: int, sb: SupabaseClient) -> dict:
    result = sb.table("protocols").select("*, query_history(*)").eq("id", protocol_id).maybe_single().execute()
    p = result.data
    if not p:
        return {"erro": "Protocolo não encontrado"}

    resultado = _scrape_url(p["url_consulta"]) if p.get("url_consulta") else _simulate_query(p)

    historico = sorted(p.get("query_history") or [], key=lambda x: x.get("data_consulta") or "")
    ultimo = historico[-1] if historico else None

    protocolo_num = p.get("protocolo", str(protocol_id))
    mudancas = _build_mudancas(ultimo, resultado, protocolo_num)
    houve_mudanca = bool(mudancas)

    now = datetime.now(timezone.utc).isoformat()

    sb.table("query_history").insert({
        "protocol_id": protocol_id,
        "status_consultado": resultado["status_consultado"],
        "situacao_consultada": resultado.get("situacao_consultada"),
        "observacao": resultado["observacao"],
        "texto_bruto": resultado["texto_bruto"],
        "houve_mudanca": houve_mudanca,
        "erro": resultado["erro"],
        "data_consulta": now,
        "data_movimentacao": resultado.get("data_movimentacao"),
        "mudancas_detectadas": json.dumps(mudancas, ensure_ascii=False) if mudancas else None,
    }).execute()

    update_payload = {"ultima_consulta": now, "observacao_consulta": resultado["observacao"]}
    if resultado["status_consultado"] and not resultado["erro"]:
        update_payload["status"] = resultado["status_consultado"]
    sb.table("protocols").update(update_payload).eq("id", protocol_id).execute()

    return {
        "protocolo": p["protocolo"],
        "resultado": resultado,
        "houve_mudanca": houve_mudanca,
        "mudancas_detectadas": mudancas,
    }


def run_all_queries(sb: SupabaseClient):
    protocols = sb.table("protocols").select("id").eq("ativo", True).execute().data
    for p in protocols:
        run_single_query(p["id"], sb)
