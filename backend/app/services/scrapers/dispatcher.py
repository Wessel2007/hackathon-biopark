"""
Central dispatcher: identifica o scraper correto pelo órgão/site e retorna
o formato interno esperado por scraper.py (_query_source).

Cada scraper individual retorna o formato padrão:
{
    "success": bool,
    "protocol": str,
    "status": str | None,
    "observation": str | None,
    "updatedAt": str | None,   # data de movimentação "DD/MM/YYYY"
    "rawText": str | None,
    "error": str | None,
    # campos extras (prefixo _) usados apenas internamente:
    "_fonte": str,
    "_situacao": str | None,   # "NAO_ENCONTRADO" quando aplicável
    "_screenshot": str | None, # base64 PNG
}
"""

import unicodedata


def _norm(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii").lower()


def _to_internal(result: dict) -> dict:
    """Converte o formato do scraper para o formato interno de scraper.py."""
    return {
        "status_consultado":   result.get("status"),
        "situacao_consultada": result.get("_situacao"),
        "observacao":          result.get("observation"),
        "texto_bruto":         result.get("rawText"),
        "screenshot_base64":   result.get("_screenshot"),
        "data_movimentacao":   result.get("updatedAt"),
        "fonte_consulta":      result.get("_fonte", "SIMULADO"),
        "erro":                result.get("error"),
    }


def _select_scraper(orgao: str, url: str):
    """Seleciona a função query() do scraper correto."""
    norm = _norm(orgao)

    if (
        "acompanhamento-de-solicitacoes" in url
        or "slwweb/publico/acompanhamento" in url
    ):
        from app.services.scrapers.copel_distribuicao import query
        return query

    if "copel" in norm or "copel" in url:
        from app.services.scrapers.copel import query
        return query

    if "sanepar" in norm or "sanepar" in url:
        from app.services.scrapers.sanepar import query
        return query

    # CBPR — consulta real no ePROTOCOLO; demais URLs do bombeiro seguem simulado
    if "eprotocolo" in url or "eprotocolo.pr.gov.br" in url:
        from app.services.scrapers.eprotocolo_pr import query
        return query

    if "bombeiro" in norm or "cbpr" in norm or "cbmpr" in norm or "cbpr" in url or "bombeiros.pr" in url:
        from app.services.scrapers.bombeiros import query
        return query

    if "sema" in norm or ("iat" in norm and "pr" in norm) or "iat.pr.gov" in url or "sema.pr.gov" in url:
        from app.services.scrapers.sema import query
        return query

    if "caixa" in norm or "cef" in norm or "caixa.gov" in url or "caixa.economica" in norm:
        from app.services.scrapers.caixa import query
        return query

    if (
        "prefeitura" in norm
        or "municipio" in norm
        or "pmtoledo" in url
        or "pmt.pr.gov" in url
        or ".pr.gov.br" in url
    ):
        from app.services.scrapers.prefeitura import query
        return query

    from app.services.scrapers.default import query
    return query


def check_protocol_status(p: dict) -> dict:
    """
    Ponto de entrada central.
    Recebe o dict do protocolo (linha da tabela protocols), identifica o scraper
    correto, executa a consulta e retorna o formato interno de scraper.py.
    """
    orgao     = (p.get("orgao_site_consultado") or "").strip()
    url       = (p.get("url_consulta") or "").strip().lower()
    protocolo = (p.get("protocolo") or "").strip()

    try:
        scraper_fn = _select_scraper(orgao, url)
        result = scraper_fn(protocolo, orgao, url)
    except Exception as exc:
        result = {
            "success":     False,
            "protocol":    protocolo,
            "status":      None,
            "observation": None,
            "updatedAt":   None,
            "rawText":     None,
            "error":       f"Erro inesperado no scraper: {str(exc)[:300]}",
            "_fonte":      f"SIMULADO: {orgao}" if orgao else "SIMULADO",
            "_situacao":   None,
            "_screenshot": None,
        }

    return _to_internal(result)
