"""
Scraper real para consulta de protocolo da SANEPAR no ePROTOCOLO (Governo do PR).

Fluxo:
- Abre consultarProtocoloDigital.do?action=iniciarProcesso
- Preenche #numeroProtocolo e clica em #btnPesquisar
- Extrai Último Andamento: Local de Envio, Onde está, Motivo, Enviado em e dias em trâmite
"""

from __future__ import annotations

from app.services.scrapers.eprotocolo_pr import query_protocol as _query_eprotocolo

URL = (
    "https://www.eprotocolo.pr.gov.br/spiweb/consultarProtocoloDigital.do"
    "?action=iniciarProcesso"
)
FONTE = "SANEPAR — Companhia de Saneamento do Paraná (ePROTOCOLO PR)"
PORTAL_LABEL = "SANEPAR — Companhia de Saneamento do Paraná"


def query(protocol: str, orgao: str, url: str) -> dict:
    return query_protocol(
        {
            "protocolo": protocol,
            "url_consulta": url,
            "orgao_site_consultado": orgao,
        }
    )


def query_protocol(p: dict) -> dict:
    payload = dict(p)
    if not (payload.get("url_consulta") or "").strip():
        payload["url_consulta"] = URL
    return _query_eprotocolo(
        payload,
        fonte=FONTE,
        default_url=URL,
        portal_label=PORTAL_LABEL,
    )
