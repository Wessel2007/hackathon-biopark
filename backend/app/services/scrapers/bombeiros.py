"""
Scraper para Corpo de Bombeiros do Paraná (CBPR).

O sistema CBPR exige login no portal cbpr.pr.gov.br para consulta de
processos de AVCB (Auto de Vistoria do Corpo de Bombeiros). Este módulo
simula o fluxo de consulta de aprovação de projetos de segurança contra incêndio.
"""

import random
from datetime import datetime, timedelta


_FONTE = "SIMULADO: Corpo de Bombeiros do Paraná — CBPR"

_STATUSES = [
    (
        "EM ANÁLISE",
        "Processo {protocolo} em análise pelo Setor Técnico do CBPR. "
        "O projeto de segurança contra incêndio está sendo avaliado conforme as normas ABNT.",
    ),
    (
        "AGUARDANDO DOCUMENTAÇÃO",
        "Processo {protocolo} com exigências. Complementar a documentação: "
        "ART do projeto, planta baixa atualizada e memorial descritivo. Prazo: 30 dias.",
    ),
    (
        "APROVADO",
        "Processo {protocolo} aprovado pelo CBPR. AVCB (Auto de Vistoria) disponível "
        "para retirada na sede do Corpo de Bombeiros local. Validade: 3 anos.",
    ),
    (
        "AGUARDANDO VISTORIA",
        "Processo {protocolo} com projeto aprovado. Aguardando agendamento de vistoria "
        "presencial para verificação dos sistemas de combate a incêndio instalados.",
    ),
    (
        "REPROVADO",
        "Processo {protocolo} reprovado na vistoria técnica. "
        "Pendências identificadas conforme relatório. Adequar e solicitar nova vistoria.",
    ),
    (
        "CANCELADO",
        "Processo {protocolo} cancelado por decurso de prazo. "
        "Protocolar novo processo com documentação atualizada.",
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

    days_ago = random.randint(0, 45)
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
