"""
Scraper padrão (fallback) para órgãos sem scraper específico.

Utilizado quando nenhum outro scraper corresponde ao orgao_site_consultado.
Simula uma consulta genérica com status realistas.
"""

import random
from datetime import datetime, timedelta


_STATUSES = [
    (
        "EM ANÁLISE",
        "Protocolo {protocolo} localizado no sistema de {orgao}. "
        "Processo em análise pelo setor responsável.",
    ),
    (
        "AGUARDANDO DOCUMENTAÇÃO",
        "Protocolo {protocolo} com pendências no sistema de {orgao}. "
        "Aguardando complementação de documentação.",
    ),
    (
        "APROVADO",
        "Protocolo {protocolo} aprovado no sistema de {orgao}. "
        "Entrar em contato com o órgão para retirada do documento.",
    ),
    (
        "PENDENTE",
        "Protocolo {protocolo} aguardando análise no sistema de {orgao}. "
        "Sem movimentação registrada nos últimos dias.",
    ),
]

_NOT_FOUND_CHANCE = 0.05  # 5% de chance de não encontrar


def _error(protocol: str, orgao: str, msg: str) -> dict:
    return {
        "success":     False,
        "protocol":    protocol,
        "status":      None,
        "observation": None,
        "updatedAt":   None,
        "rawText":     None,
        "error":       msg,
        "_fonte":      f"SIMULADO: {orgao}" if orgao else "SIMULADO",
        "_situacao":   None,
        "_screenshot": None,
    }


def query(protocol: str, orgao: str, url: str) -> dict:
    if not protocol or not orgao:
        return _error(
            protocol, orgao,
            "Protocolo ou órgão não informado — consulta não realizada.",
        )

    days_ago = random.randint(0, 45)
    data_mov = (datetime.now() - timedelta(days=days_ago)).strftime("%d/%m/%Y")
    fonte = f"SIMULADO: {orgao}"

    if random.random() < _NOT_FOUND_CHANCE:
        return {
            "success":     True,
            "protocol":    protocol,
            "status":      None,
            "observation": f"Protocolo {protocol} não localizado no sistema de {orgao}.",
            "updatedAt":   data_mov,
            "rawText":     None,
            "error":       None,
            "_fonte":      fonte,
            "_situacao":   "NAO_ENCONTRADO",
            "_screenshot": None,
        }

    status, obs_template = random.choice(_STATUSES)
    obs = obs_template.format(protocolo=protocol, orgao=orgao)

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
