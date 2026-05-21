from datetime import datetime, timezone, timedelta
import random
import re
import json
import time
from html import unescape

import httpx
from bs4 import BeautifulSoup

from app.supabase_client import SupabaseClient


# ---------------------------------------------------------------------------
# Real source: e-Andamento Cartorios PR (Toledo - 1o Oficio)
# ---------------------------------------------------------------------------

_CARTORIOS_PR_URL = "https://www.cartoriospr.com.br/eandamento/index.php?modulo=resultado&token="
_TOLEDO_1_OFICIO = {
    "serventia": "193",
    "cns": "88401",
    "pedido_balcao": "S",
    "download_direto": "S",
    "tipo": "1",  # Protocolo de Registro/Averbacoes
}


def _only_digits(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def _is_cartorios_pr_query(p: dict) -> bool:
    orgao = (p.get("orgao_site_consultado") or "").lower()
    url = (p.get("url_consulta") or "").lower()
    return (
        "cartoriospr.com.br" in url
        or "toledo" in orgao
    )


def _label_value(text: str, label: str) -> str | None:
    pattern = rf"{re.escape(label)}:\s*(.*?)(?=\s*(?:Data Movimentação|Setor|Posição de serviço):|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return " ".join(match.group(1).split()) or None


def _parse_cartorios_pr_result(html: str, protocolo: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    page_text = " ".join(soup.get_text(" ", strip=True).split())

    if "O número digitado não foi encontrado" in page_text:
        return {
            "status_consultado": None,
            "situacao_consultada": "NAO_ENCONTRADO",
            "observacao": f"Protocolo {protocolo} nao localizado no e-Andamento do Cartorios PR.",
            "texto_bruto": None,
            "data_movimentacao": None,
            "fonte_consulta": "REAL: Cartorios PR e-Andamento - Toledo 1o Oficio",
            "erro": None,
        }

    movements: list[dict[str, str | None]] = []
    for item in soup.select("ul.list-group li.list-group-item"):
        text = " ".join(item.get_text(" ", strip=True).split())
        movement = {
            "data_movimentacao": _label_value(text, "Data Movimentação"),
            "setor": _label_value(text, "Setor"),
            "posicao_servico": _label_value(text, "Posição de serviço"),
        }
        if movement["data_movimentacao"] or movement["posicao_servico"]:
            movements.append(movement)

    if not movements:
        return {
            "status_consultado": None,
            "situacao_consultada": None,
            "observacao": "Consulta concluida, mas o andamento do servico nao foi encontrado no HTML retornado.",
            "texto_bruto": page_text[:4000],
            "data_movimentacao": None,
            "fonte_consulta": "REAL: Cartorios PR e-Andamento - Toledo 1o Oficio",
            "erro": "Nao foi possivel identificar a ultima movimentacao no retorno do Cartorios PR.",
        }

    latest = movements[-1]
    posicao = latest.get("posicao_servico") or "CONSULTADO"
    setor = latest.get("setor")
    data_mov = latest.get("data_movimentacao")

    return {
        "status_consultado": posicao.upper(),
        "situacao_consultada": None,
        "observacao": f"Ultima movimentacao: {data_mov} | Setor: {setor or '-'} | Posicao de servico: {posicao}",
        "texto_bruto": json.dumps(
            {"fonte": "cartoriospr_eandamento", "movimentacoes": movements},
            ensure_ascii=False,
        ),
        "data_movimentacao": data_mov,
        "fonte_consulta": "REAL: Cartorios PR e-Andamento - Toledo 1o Oficio",
        "erro": None,
    }


def _query_cartorios_pr_toledo(p: dict) -> dict:
    protocolo = _only_digits(p.get("protocolo"))
    if not protocolo:
        return {
            "status_consultado": None,
            "situacao_consultada": None,
            "observacao": None,
            "texto_bruto": None,
            "data_movimentacao": None,
            "fonte_consulta": "REAL: Cartorios PR e-Andamento - Toledo 1o Oficio",
            "erro": "Protocolo vazio ou invalido para consulta no Cartorios PR.",
        }

    payload = {**_TOLEDO_1_OFICIO, "protocolo": protocolo, "chave_edownload": ""}
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; HackathonBiopark/1.0; consulta-protocolos)",
        "Referer": "https://www.cartoriospr.com.br/eandamento/index.php?token=",
    }

    try:
        with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
            response = client.post(_CARTORIOS_PR_URL, data=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return {
            "status_consultado": None,
            "situacao_consultada": None,
            "observacao": None,
            "texto_bruto": None,
            "data_movimentacao": None,
            "fonte_consulta": "REAL: Cartorios PR e-Andamento - Toledo 1o Oficio",
            "erro": f"Falha ao consultar Cartorios PR: {exc}",
        }

    return _parse_cartorios_pr_result(unescape(response.text), protocolo)


# ---------------------------------------------------------------------------
# Mock simulation (hackathon mode — no real HTTP requests)
# ---------------------------------------------------------------------------

_ORGAN_STATUSES: dict[str, list[str]] = {
    "prefeitura": ["EM ANÁLISE", "APROVADO", "AGUARDANDO DOCUMENTAÇÃO"],
    "copel":      ["EM ANÁLISE", "AGUARDANDO VISTORIA", "APROVADO"],
    "cartório":   ["EM ANÁLISE", "REGISTRADO", "CANCELADO"],
    "cartorio":   ["EM ANÁLISE", "REGISTRADO", "CANCELADO"],
}

_ORGAN_OBSERVATIONS: dict[str, dict[str, str]] = {
    "prefeitura": {
        "EM ANÁLISE":              "Processo em análise técnica. Aguardando parecer da equipe responsável.",
        "APROVADO":                "Licença aprovada. Documentação disponível para retirada no protocolo.",
        "AGUARDANDO DOCUMENTAÇÃO": "Processo suspenso. Necessário protocolar documentação complementar indicada no ofício.",
    },
    "copel": {
        "EM ANÁLISE":         "Solicitação em análise pelo setor técnico da distribuidora.",
        "AGUARDANDO VISTORIA":"Aguardando agendamento de vistoria presencial no local da obra.",
        "APROVADO":           "Conexão aprovada. Entrar em contato para agendamento da ligação.",
    },
    "cartório": {
        "EM ANÁLISE": "Documentação em análise pelo registrador.",
        "REGISTRADO": "Registro efetivado. Certidão disponível para retirada.",
        "CANCELADO":  "Pedido cancelado a pedido do requerente ou por ausência de requisitos.",
    },
    "cartorio": {
        "EM ANÁLISE": "Documentação em análise pelo registrador.",
        "REGISTRADO": "Registro efetivado. Certidão disponível para retirada.",
        "CANCELADO":  "Pedido cancelado a pedido do requerente ou por ausência de requisitos.",
    },
}


def _organ_key(orgao: str) -> str:
    lower = orgao.lower()
    for key in _ORGAN_STATUSES:
        if key in lower:
            return key
    return "outros"


def _mock_query(p: dict) -> dict:
    protocolo = (p.get("protocolo") or "").strip()
    orgao = (p.get("orgao_site_consultado") or "").strip()

    if not protocolo or not orgao:
        return {
            "status_consultado":  None,
            "situacao_consultada": None,
            "observacao":         None,
            "texto_bruto":        None,
            "data_movimentacao":  None,
            "fonte_consulta":     f"SIMULADO: {orgao}" if orgao else "SIMULADO",
            "erro": "Protocolo ou órgão não informado — consulta não realizada.",
        }

    key = _organ_key(orgao)
    days_ago = random.randint(0, 45)
    data_mov = (datetime.now() - timedelta(days=days_ago)).strftime("%d/%m/%Y")

    if key == "outros":
        status = random.choice(["CONSULTADO", "NÃO ENCONTRADO"])
        if status == "NÃO ENCONTRADO":
            return {
                "status_consultado":  None,
                "situacao_consultada": "NAO_ENCONTRADO",
                "observacao":  f"Protocolo {protocolo} não localizado no sistema de {orgao}.",
                "texto_bruto": None,
                "data_movimentacao": data_mov,
                "fonte_consulta": f"SIMULADO: {orgao}",
                "erro": None,
            }
        obs = f"Protocolo {protocolo} localizado no sistema de {orgao}. Consulta realizada com sucesso."
    else:
        status = random.choice(_ORGAN_STATUSES[key])
        template = (_ORGAN_OBSERVATIONS.get(key) or {}).get(status, "")
        obs = f"Protocolo {protocolo} — {template}" if template else f"Protocolo {protocolo}: {status}."

    return {
        "status_consultado":   status,
        "situacao_consultada": None,
        "observacao":          obs,
        "texto_bruto":         None,
        "data_movimentacao":   data_mov,
        "fonte_consulta":      f"SIMULADO: {orgao}",
        "erro":                None,
    }


def _query_source(p: dict) -> dict:
    if _is_cartorios_pr_query(p):
        return _query_cartorios_pr_toledo(p)
    return _mock_query(p)


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------

def _build_mudancas(ultimo: dict | None, resultado: dict, protocolo_num: str) -> list[str]:
    mudancas: list[str] = []
    num = protocolo_num

    if resultado.get("erro"):
        if not (ultimo or {}).get("erro"):
            mudancas.append(f"Protocolo {num}: consulta retornou erro")
        return mudancas

    if ultimo and ultimo.get("erro"):
        mudancas.append(f"Protocolo {num}: consulta voltou a responder com sucesso")

    not_found_now    = resultado.get("situacao_consultada") == "NAO_ENCONTRADO"
    not_found_before = (ultimo or {}).get("situacao_consultada") == "NAO_ENCONTRADO"

    if not_found_now and not not_found_before:
        mudancas.append(f"Protocolo {num} deixou de ser encontrado no sistema")
        return mudancas
    if not_found_now:
        return mudancas

    if not ultimo:
        return mudancas

    status_ant = ultimo.get("status_consultado")
    status_nov = resultado.get("status_consultado")
    if status_ant and status_nov and status_ant != status_nov:
        mudancas.append(f'Protocolo {num} mudou de "{status_ant}" para "{status_nov}"')

    obs_ant = (ultimo.get("observacao") or "").strip()
    obs_nov = (resultado.get("observacao") or "").strip()
    if obs_nov and not obs_ant:
        mudancas.append(f"Protocolo {num}: nova observação registrada")
    elif obs_nov and obs_ant and obs_nov != obs_ant:
        mudancas.append(f"Protocolo {num}: observação foi atualizada")

    data_ant = (ultimo.get("data_movimentacao") or "").strip()
    data_nov = (resultado.get("data_movimentacao") or "").strip()
    if data_nov and not data_ant:
        mudancas.append(f"Protocolo {num}: nova data de movimentação registrada ({data_nov})")
    elif data_nov and data_ant and data_nov != data_ant:
        mudancas.append(f"Protocolo {num}: data de movimentação mudou de {data_ant} para {data_nov}")

    return mudancas


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def run_single_query(protocol_id: int, sb: SupabaseClient) -> dict:
    result = (
        sb.table("protocols")
        .select("*, query_history(*)")
        .eq("id", protocol_id)
        .maybe_single()
        .execute()
    )
    p = result.data
    if not p:
        return {"erro": "Protocolo não encontrado"}

    resultado = _query_source(p)

    historico = sorted(
        p.get("query_history") or [],
        key=lambda x: x.get("data_consulta") or "",
    )
    ultimo = historico[-1] if historico else None

    protocolo_num = p.get("protocolo", str(protocol_id))
    mudancas      = _build_mudancas(ultimo, resultado, protocolo_num)
    houve_mudanca = bool(mudancas)

    status_anterior = (ultimo.get("status_consultado") if ultimo else None) or p.get("status")
    status_novo     = resultado.get("status_consultado")

    now = datetime.now(timezone.utc).isoformat()

    sb.table("query_history").insert({
        "protocol_id":        protocol_id,
        "status_consultado":  resultado["status_consultado"],
        "situacao_consultada": resultado.get("situacao_consultada"),
        "observacao":         resultado["observacao"],
        "texto_bruto":        resultado["texto_bruto"],
        "houve_mudanca":      houve_mudanca,
        "erro":               resultado["erro"],
        "data_consulta":      now,
        "data_movimentacao":  resultado.get("data_movimentacao"),
        "mudancas_detectadas": json.dumps(mudancas, ensure_ascii=False) if mudancas else None,
        "fonte_consulta":     resultado.get("fonte_consulta"),
        "status_anterior":    status_anterior,
    }).execute()

    update_payload: dict = {
        "ultima_consulta":    now,
        "observacao_consulta": resultado["observacao"],
    }
    if resultado["status_consultado"] and not resultado["erro"]:
        update_payload["status"] = resultado["status_consultado"]
    sb.table("protocols").update(update_payload).eq("id", protocol_id).execute()

    return {
        "protocolo":         p["protocolo"],
        "resultado": {
            **resultado,
            "data_hora_consulta": now,
        },
        "houve_mudanca":      houve_mudanca,
        "mudancas_detectadas": mudancas,
        "status_anterior":    status_anterior,
        "status_novo":        status_novo,
        "erro":               resultado.get("erro"),
    }


def run_all_queries(sb: SupabaseClient) -> None:
    protocols = sb.table("protocols").select("id").eq("ativo", True).execute().data
    for p in (protocols or []):
        run_single_query(p["id"], sb)
        time.sleep(1)
