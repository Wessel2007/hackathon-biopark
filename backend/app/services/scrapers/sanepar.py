"""
Scraper para SANEPAR (Companhia de Saneamento do Paraná).

O portal da SANEPAR exige autenticação para rastreamento de protocolos de
obra, tornando automação direta inviável. Este módulo simula consultas de
solicitações de ligação de água e esgoto.
"""

import random
from datetime import datetime, timedelta


_FONTE = "SIMULADO: SANEPAR — Companhia de Saneamento do Paraná"

_STATUSES = [
    (
        "EM ANÁLISE",
        "Solicitação {protocolo} em análise técnica pelo setor de Projetos e Obras da SANEPAR. "
        "Prazo estimado: 20 dias úteis para emissão de parecer.",
    ),
    (
        "AGUARDANDO VISTORIA",
        "Solicitação {protocolo} com documentação aprovada. Aguardando agendamento de "
        "vistoria técnica no local para verificação das condições de ligação.",
    ),
    (
        "APROVADO",
        "Solicitação {protocolo} aprovada. Ligação de água e esgoto autorizada. "
        "A execução será realizada pela SANEPAR em até 15 dias úteis após confirmação.",
    ),
    (
        "AGUARDANDO DOCUMENTAÇÃO",
        "Solicitação {protocolo} suspensa. Apresentar: Certidão de Uso do Solo, "
        "Habite-se ou Alvará de Construção atualizado. Prazo: 30 dias para regularização.",
    ),
    (
        "REPROVADO",
        "Solicitação {protocolo} indeferida. Não conformidade com normas técnicas "
        "da SANEPAR. Consultar o laudo técnico disponível no portal do cliente.",
    ),
]


def _error(protocol: str, msg: str) -> dict:
    return {
        "success":     False,
        "protocol":    protocol,
        "status":      None,
        "observation": None,
        "updatedAt":   None,
        "rawText":     None,
        "error":       msg,
        "_fonte":      _FONTE,
        "_situacao":   None,
        "_screenshot": None,
    }


def query(protocol: str, orgao: str, url: str) -> dict:
    if not protocol:
        return _error(protocol, "Número do protocolo não informado — consulta não realizada.")

    days_ago = random.randint(0, 30)
    data_mov = (datetime.now() - timedelta(days=days_ago)).strftime("%d/%m/%Y")

    status, obs_template = random.choice(_STATUSES)
    obs = obs_template.format(protocolo=protocol)

    return {
        "success":     True,
        "protocol":    protocol,
        "status":      status,
        "observation": obs,
        "updatedAt":   data_mov,
        "rawText":     None,
        "error":       None,
        "_fonte":      _FONTE,
        "_situacao":   None,
        "_screenshot": None,
    }
