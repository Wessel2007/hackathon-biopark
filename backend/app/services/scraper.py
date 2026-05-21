from datetime import datetime, timezone, timedelta
import random
import re
import json

from app.supabase_client import SupabaseClient


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
            "fonte_consulta":     orgao or None,
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
                "fonte_consulta": orgao,
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
        "fonte_consulta":      orgao,
        "erro":                None,
    }


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

    resultado = _mock_query(p)

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
