"""
Scraper real para acompanhamento de solicitações — COPEL Distribuição.

Portal público:
https://www.copel.com/site/copel-distribuicao/acompanhamento-de-solicitacoes/

O formulário roda em iframe (slwweb/publico/acompanhamento/inicio.jsf).
"""

from __future__ import annotations

import base64
import concurrent.futures
import json
import re
from typing import Any


URL = (
    "https://www.copel.com/site/copel-distribuicao/"
    "acompanhamento-de-solicitacoes/"
)
URL_JSF = "https://www.copel.com/slwweb/publico/acompanhamento/inicio.jsf"
FONTE = "COPEL Distribuição — Acompanhamento de Solicitações"

_INPUT = 'input[name="formPrincipal:j_idt23"]'
_BTN = 'button[id="formPrincipal:btnPesquisar"]'


def _normalize_protocol(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").strip())


def _error(protocol: str, msg: str, situacao: str | None = None) -> dict:
    return {
        "success": False,
        "protocol": protocol,
        "status": None,
        "observation": None,
        "updatedAt": None,
        "rawText": None,
        "error": msg,
        "_fonte": FONTE,
        "_situacao": situacao,
        "_screenshot": None,
    }


def _map_status(descricao: str) -> str | None:
    upper = (descricao or "").upper()
    haystack = f"{upper} {upper.encode('ascii', 'ignore').decode('ascii')}"
    patterns = [
        ("CANCELADO", "CANCELADO"),
        ("CANCELADA", "CANCELADO"),
        ("INDEFERIDO", "REPROVADO"),
        ("REPROVADO", "REPROVADO"),
        ("NEGADO", "REPROVADO"),
        ("DEFERIDO", "APROVADO"),
        ("APROVADO", "APROVADO"),
        ("APROVADA", "APROVADO"),
        ("FINALIZADO", "APROVADO"),
        ("FINALIZADA", "APROVADO"),
        ("CONCLUIDO", "APROVADO"),
        ("CONCLUÍDA", "APROVADO"),
        ("CONCLUIDA", "APROVADO"),
        ("EXECUTADO", "APROVADO"),
        ("LIGACAO", "APROVADO"),
        ("LIGAÇÃO", "APROVADO"),
        ("VISTORIA", "PENDENTE"),
        ("PENDENTE", "PENDENTE"),
        ("EXIGENCIA", "PENDENTE"),
        ("EXIGÊNCIA", "PENDENTE"),
        ("AGUARDANDO", "PENDENTE"),
        ("ORCAMENTO", "EM ANDAMENTO"),
        ("ORÇAMENTO", "EM ANDAMENTO"),
        ("ANALISE", "EM ANDAMENTO"),
        ("ANÁLISE", "EM ANDAMENTO"),
        ("TRAMITE", "EM ANDAMENTO"),
        ("TRÂMITE", "EM ANDAMENTO"),
    ]
    for needle, status in patterns:
        if needle in haystack:
            return status
    return "EM ANDAMENTO" if descricao else None


def _clean_cell(text: str, label: str) -> str:
    value = re.sub(r"\s+", " ", (text or "").strip())
    prefix = re.compile(rf"^{re.escape(label)}\s*", re.I)
    return prefix.sub("", value).strip()


def _extract_movimentos_from_page(page: Any) -> list[dict[str, str]]:
    try:
        rows = page.evaluate(
            """
            () => {
              const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
              return [...document.querySelectorAll('.ui-datatable-data tr[role=row]')].map((row) => {
                const cells = [...row.querySelectorAll('[role=gridcell]')].map((cell) => norm(cell.innerText));
                return { sequencia: cells[0] || '', descricao: cells[1] || '' };
              }).filter((item) => item.sequencia || item.descricao);
            }
            """
        )
        if not isinstance(rows, list):
            return []
        result: list[dict[str, str]] = []
        for row in rows:
            sequencia = _clean_cell(str(row.get("sequencia") or ""), "Sequência")
            descricao = _clean_cell(str(row.get("descricao") or ""), "Descrição")
            if descricao:
                result.append({"sequencia": sequencia, "descricao": descricao})
        return result
    except Exception:
        return []


def _extract_movimentos_from_html(html: str) -> list[dict[str, str]]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    soup = BeautifulSoup(html or "", "html.parser")
    result: list[dict[str, str]] = []
    for row in soup.select(".ui-datatable-data tr[role=row]"):
        cells = [cell.get_text(" ", strip=True) for cell in row.select("[role=gridcell]")]
        if len(cells) < 2:
            continue
        descricao = _clean_cell(cells[1], "Descrição")
        if descricao:
            result.append({
                "sequencia": _clean_cell(cells[0], "Sequência"),
                "descricao": descricao,
            })
    return result


def _build_observation(protocol: str, movimentos: list[dict[str, str]]) -> str:
    parts = [f"Solicitacao {protocol} consultada na COPEL Distribuicao."]
    for item in movimentos:
        seq = item.get("sequencia")
        desc = item.get("descricao")
        if seq and desc:
            parts.append(f"Sequencia {seq}: {desc}.")
        elif desc:
            parts.append(f"{desc}.")
    return " ".join(parts)


def _parse_result(
    body_text: str,
    protocol: str,
    movimentos: list[dict[str, str]],
) -> tuple[str | None, str, str | None, str | None]:
    clean_text = re.sub(r"\s+", " ", body_text or "").strip()
    invalid = re.search(
        r"inv[aá]lido|n[aã]o encontrado|nao encontrado|sem resultado|inexistente",
        clean_text,
        re.I,
    )

    if invalid and not movimentos:
        msg_match = re.search(
            r"((?:verifique|foi digitado)[^.]*\.?|n[aã]o encontrado[^.]*)",
            clean_text,
            re.I,
        )
        detalhe = msg_match.group(1).strip() if msg_match else "solicitacao nao localizada"
        return None, f"Solicitacao {protocol} — {detalhe} (COPEL).", None, "NAO_ENCONTRADO"

    if not movimentos:
        return (
            None,
            f"Consulta COPEL executada, mas nenhuma etapa foi extraida para a solicitacao {protocol}.",
            None,
            "SEM_DADOS_EXTRAIDOS",
        )

    latest = movimentos[-1]
    descricao = latest.get("descricao") or ""
    status = _map_status(descricao)
    observation = _build_observation(protocol, movimentos)
    date_match = re.search(r"(\d{2}/\d{2}/\d{4})", clean_text)
    updated_at = date_match.group(1) if date_match else None
    return status, observation, updated_at, None


def _resolve_form_page(page: Any, url: str) -> Any:
    from playwright.sync_api import TimeoutError as PWTimeout

    target = (url or "").strip() or URL
    lower = target.lower()
    if "slwweb/publico/acompanhamento" in lower:
        page.goto(target, wait_until="domcontentloaded", timeout=60000)
        return page

    page.goto(target, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except PWTimeout:
        pass

    try:
        page.wait_for_function(
            """
            () => {
              const inFrames = window.frames.length > 1;
              const iframe = [...document.querySelectorAll('iframe')].some((el) =>
                (el.src || '').includes('slwweb/publico/acompanhamento')
              );
              return inFrames || iframe;
            }
            """,
            timeout=45000,
        )
    except PWTimeout:
        pass

    frame = page.frame(url=lambda u: u and "slwweb/publico/acompanhamento" in (u or ""))
    if frame is None:
        page.goto(URL_JSF, wait_until="domcontentloaded", timeout=60000)
        return page
    return frame


def _fill_and_search(form_page: Any, numero: str) -> bool:
    input_el = form_page.locator(_INPUT).first
    input_el.wait_for(state="visible", timeout=20000)
    input_el.click()
    input_el.fill(numero)
    button = form_page.locator(_BTN).first
    if not button.count():
        return False
    button.click()
    return True


def _wait_for_result(form_page: Any) -> None:
    from playwright.sync_api import TimeoutError as PWTimeout

    try:
        form_page.wait_for_function(
            """
            () => {
              const rows = document.querySelectorAll('.ui-datatable-data tr[role=row]').length;
              const body = (document.body?.innerText || '').toLowerCase();
              const err = /inv[aá]lido|invalido|n[aã]o encontrado|nao encontrado/.test(body);
              return rows > 0 || err;
            }
            """,
            timeout=25000,
        )
    except PWTimeout:
        pass

    try:
        form_page.wait_for_load_state("networkidle", timeout=12000)
    except PWTimeout:
        pass
    form_page.wait_for_timeout(1500)


def _sync_query(protocol: str, numero: str, url: str) -> dict:
    try:
        from playwright.sync_api import TimeoutError as PWTimeout
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _error(protocol, "Playwright nao instalado.")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        form_page = _resolve_form_page(page, url)
        try:
            form_page.wait_for_load_state("networkidle", timeout=15000)
        except PWTimeout:
            pass

        if not _fill_and_search(form_page, numero):
            browser.close()
            return _error(protocol, "Formulario de consulta COPEL nao localizado.")

        _wait_for_result(form_page)

        screenshot = page.screenshot(full_page=True)
        html = form_page.content()
        body_text = form_page.locator("body").inner_text(timeout=5000)
        movimentos = _extract_movimentos_from_page(form_page)
        if not movimentos:
            movimentos = _extract_movimentos_from_html(html)
        browser.close()

    status, observation, updated_at, situacao = _parse_result(body_text, protocol, movimentos)
    raw_payload = {"movimentos": movimentos, "solicitacao_consultada": numero}
    raw_text = (
        f"COPEL_DISTRIBUICAO={json.dumps(raw_payload, ensure_ascii=False)}\n"
        f"{html[:6500] if html else ''}"
    )[:8000]

    screenshot_b64 = base64.b64encode(screenshot).decode()

    if situacao == "NAO_ENCONTRADO":
        return {
            "success": True,
            "protocol": protocol,
            "status": None,
            "observation": observation,
            "updatedAt": updated_at,
            "rawText": raw_text,
            "error": None,
            "_fonte": FONTE,
            "_situacao": situacao,
            "_screenshot": screenshot_b64,
        }

    if situacao == "SEM_DADOS_EXTRAIDOS":
        return {
            "success": False,
            "protocol": protocol,
            "status": None,
            "observation": observation,
            "updatedAt": updated_at,
            "rawText": raw_text,
            "error": observation,
            "_fonte": FONTE,
            "_situacao": situacao,
            "_screenshot": screenshot_b64,
        }

    return {
        "success": True,
        "protocol": protocol,
        "status": status,
        "observation": observation,
        "updatedAt": updated_at,
        "rawText": raw_text,
        "error": None,
        "_fonte": FONTE,
        "_situacao": situacao,
        "_screenshot": screenshot_b64,
    }


def query(protocol: str, orgao: str, url: str) -> dict:
    return query_protocol({
        "protocolo": protocol,
        "url_consulta": url,
        "orgao_site_consultado": orgao,
    })


def query_protocol(p: dict) -> dict:
    protocol = (p.get("protocolo") or "").strip()
    if not protocol:
        return _error(protocol, "Numero da solicitacao nao informado - consulta nao realizada.")

    numero = _normalize_protocol(protocol)
    if not numero:
        return _error(protocol, "Numero da solicitacao invalido para consulta na COPEL.")

    url = (p.get("url_consulta") or "").strip()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_sync_query, protocol, numero, url)
            return future.result(timeout=120)
    except Exception as exc:
        return _error(protocol, f"Erro na consulta COPEL: {str(exc)[:300]}")
