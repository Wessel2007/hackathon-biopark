"""
Scraper para SEMA/IAT (Secretaria de Estado do Meio Ambiente e Serviço Social /
Instituto Água e Terra do Paraná).

O portal licenciamento.iat.pr.gov.br possui captcha e requer autenticação
para consultas aprofundadas. Este módulo simula o fluxo de consulta de
Licenças Ambientais (LP, LI, LO) e autorizações ambientais.
"""

import random
from datetime import datetime, timedelta


_FONTE = "SIMULADO: IAT/SEMA — Instituto Água e Terra do Paraná"

_STATUSES = [
    (
        "EM ANÁLISE",
        "Processo {protocolo} em análise técnica ambiental pelo IAT. "
        "Equipe verificando conformidade com legislação ambiental estadual e federal.",
    ),
    (
        "AGUARDANDO DOCUMENTAÇÃO",
        "Processo {protocolo} com exigências técnicas. Complementar: EIA/RIMA, "
        "ART do responsável técnico e planilha de caracterização do empreendimento.",
    ),
    (
        "APROVADO",
        "Licença ambiental do processo {protocolo} emitida com sucesso pelo IAT. "
        "Documento disponível para download no portal licenciamento.iat.pr.gov.br.",
    ),
    (
        "AGUARDANDO VISTORIA",
        "Processo {protocolo} com documentação aprovada. "
        "Aguardando realização de vistoria de campo pela equipe técnica do IAT.",
    ),
    (
        "REPROVADO",
        "Licença ambiental do processo {protocolo} indeferida. "
        "O empreendimento não atende aos requisitos ambientais exigidos. Consultar parecer técnico.",
    ),
    (
        "CANCELADO",
        "Processo {protocolo} arquivado por inatividade. "
        "Protocolar nova solicitação com documentação atualizada para retomar o licenciamento.",
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

    days_ago = random.randint(0, 60)
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
