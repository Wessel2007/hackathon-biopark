"""
Scraper para Prefeitura Municipal.

Sites das prefeituras do Paraná geralmente exigem login ou possuem captcha,
tornando automação inviável sem credenciais. Este módulo implementa uma
simulação limpa que reproduz o fluxo real de consulta de alvará/licença.

Status retornados mapeiam para os internos via _mapear_status_sistema():
  "EM ANÁLISE"              → EM ANDAMENTO
  "AGUARDANDO DOCUMENTAÇÃO" → PENDENTE  (match parcial em "AGUARDANDO")
  "APROVADO"                → APROVADO
  "REPROVADO"               → REPROVADO
  "CANCELADO"               → CANCELADO
"""

import random
from datetime import datetime, timedelta


_FONTE_PREFIX = "SIMULADO: Prefeitura Municipal"

_STATUSES = [
    (
        "EM ANÁLISE",
        "Processo {protocolo} em análise técnica pelo setor de Engenharia e Planejamento Urbano. "
        "Prazo estimado para parecer: 15 dias úteis.",
    ),
    (
        "AGUARDANDO DOCUMENTAÇÃO",
        "Processo {protocolo} suspenso. Necessário protocolar documentação complementar "
        "conforme Notificação de Exigência emitida pelo setor responsável.",
    ),
    (
        "APROVADO",
        "Processo {protocolo} deferido. Alvará/licença disponível para retirada no "
        "Departamento de Controle Urbano. Trazer documento de identificação.",
    ),
    (
        "REPROVADO",
        "Processo {protocolo} indeferido conforme Notificação de Indeferimento. "
        "Consultar o setor responsável para verificar os motivos e possibilidade de recurso.",
    ),
    (
        "CANCELADO",
        "Processo {protocolo} cancelado a pedido do requerente ou por decurso de prazo "
        "sem manifestação. Para reativar, protocolar novo requerimento.",
    ),
]


def _error(protocol: str, orgao: str, msg: str) -> dict:
    return {
        "success":     False,
        "protocol":    protocol,
        "status":      None,
        "observation": None,
        "updatedAt":   None,
        "rawText":     None,
        "error":       msg,
        "_fonte":      f"{_FONTE_PREFIX} — {orgao}" if orgao else _FONTE_PREFIX,
        "_situacao":   None,
        "_screenshot": None,
    }


def query(protocol: str, orgao: str, url: str) -> dict:
    if not protocol:
        return _error(protocol, orgao, "Número do protocolo não informado — consulta não realizada.")

    days_ago = random.randint(0, 45)
    data_mov = (datetime.now() - timedelta(days=days_ago)).strftime("%d/%m/%Y")

    status, obs_template = random.choice(_STATUSES)
    obs = obs_template.format(protocolo=protocol)
    fonte = f"{_FONTE_PREFIX} — {orgao}" if orgao else _FONTE_PREFIX

    return {
        "success":     True,
        "protocol":    protocol,
        "status":      status,
        "observation": obs,
        "updatedAt":   data_mov,
        "rawText":     None,
        "error":       None,
        "_fonte":      fonte,
        "_situacao":   None,
        "_screenshot": None,
    }
