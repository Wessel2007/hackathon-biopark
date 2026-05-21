"""
Scraper simulado para COPEL (Companhia Paranaense de Energia).

Consultas reais no acompanhamento de solicitações (copel.com / slwweb) são feitas
por ``copel_distribuicao.py`` quando a URL aponta para esse portal.

Este módulo cobre demais fluxos da COPEL onde ainda não há automação.
"""

import random
from datetime import datetime, timedelta


_FONTE = "SIMULADO: COPEL — Companhia Paranaense de Energia"

_STATUSES = [
    (
        "EM ANÁLISE",
        "Solicitação {protocolo} recebida e em análise pelo setor técnico da distribuidora. "
        "O prazo padrão para retorno é de até 30 dias úteis.",
    ),
    (
        "AGUARDANDO VISTORIA",
        "Solicitação {protocolo} aprovada na análise documental. Aguardando agendamento "
        "de vistoria presencial no local da obra. Entre em contato para confirmar data.",
    ),
    (
        "APROVADO",
        "Solicitação {protocolo} aprovada. A conexão foi autorizada. Entre em contato com "
        "a COPEL para agendar a execução da ligação elétrica no prazo de 90 dias.",
    ),
    (
        "AGUARDANDO DOCUMENTAÇÃO",
        "Solicitação {protocolo} pendente. Documentação técnica incompleta ou com inconsistências. "
        "Verificar o ofício de exigência disponível no portal do cliente.",
    ),
    (
        "CANCELADO",
        "Solicitação {protocolo} cancelada por decurso de prazo ou a pedido do solicitante. "
        "Para reativação protocolar nova solicitação com documentação atualizada.",
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
