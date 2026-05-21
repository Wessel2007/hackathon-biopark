"""
Scraper para Caixa Econômica Federal (CEF).

O portal da Caixa (caixa.gov.br) exige autenticação CPF/senha para consulta
de financiamentos, FGTS e processos de crédito imobiliário. Este módulo
simula consultas de processos de financiamento de obra.
"""

import random
from datetime import datetime, timedelta


_FONTE = "SIMULADO: Caixa Econômica Federal — CEF"

_STATUSES = [
    (
        "EM ANÁLISE",
        "Processo {protocolo} em análise de crédito/engenharia na Caixa Econômica Federal. "
        "Prazo estimado para retorno: 10 dias úteis.",
    ),
    (
        "AGUARDANDO DOCUMENTAÇÃO",
        "Processo {protocolo} com pendências documentais. Apresentar: comprovante de renda "
        "atualizado, certidão de matrícula do imóvel e planta aprovada pela Prefeitura.",
    ),
    (
        "APROVADO",
        "Processo {protocolo} aprovado. Contrato de financiamento disponível para assinatura "
        "na agência Caixa responsável. Trazer documentos de identificação originais.",
    ),
    (
        "AGUARDANDO VISTORIA",
        "Processo {protocolo} aguardando vistoria de engenharia da CEF. "
        "Engenheiro credenciado realizará avaliação do imóvel/obra em breve.",
    ),
    (
        "REPROVADO",
        "Processo {protocolo} não aprovado. Verificar o motivo no extrato disponível "
        "no aplicativo Habitação Caixa ou comparecer à agência.",
    ),
    (
        "CANCELADO",
        "Processo {protocolo} cancelado. O prazo de validade da proposta expirou. "
        "Solicitar nova análise de crédito se ainda houver interesse.",
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
