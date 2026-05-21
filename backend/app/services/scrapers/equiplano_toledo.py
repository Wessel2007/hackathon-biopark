"""
Scraper real para consulta de processos no portal Equiplano de Toledo.

Fluxo autorizado para a empresa CARMEL:
- Processo: numero do protocolo, sem o ano quando vier no formato "123/2019"
- Exercicio: ano do protocolo ou da data de abertura
- CPF/CNPJ: 59.387.026/0001-87
- Entidade: Municipio de Toledo
"""

from __future__ import annotations

import base64
import concurrent.futures
import json
import re
from typing import Any


URL = "https://equiplano.toledo.pr.gov.br:7443/contribuinte/#/stpProcessos/pesquisa"
CNPJ_CARMEL = "59.387.026/0001-87"
ENTIDADE = "Municipio de Toledo"
FONTE = "EQUIPLANO TOLEDO - CARMEL"


def _only_digits(value: str) -> str:
    return re.sub(r"\D+", "", value or "")


def _split_process_exercise(protocol: str, data_abertura: str | None) -> tuple[str, str | None]:
    raw = (protocol or "").strip()
    match = re.search(r"(?P<processo>.*?)(?P<ano>20\d{2}|19\d{2})\s*$", raw)
    if match:
        processo = _only_digits(match.group("processo"))
        return processo or match.group("processo").strip(" -/_."), match.group("ano")

    ano_match = re.search(r"\b(20\d{2}|19\d{2})\b", raw)
    if ano_match:
        processo = raw[: ano_match.start()].strip(" -/_") or raw
        return _only_digits(processo) or processo, ano_match.group(1)

    abertura = str(data_abertura or "")
    if re.match(r"\d{4}-\d{2}-\d{2}", abertura):
        return raw, abertura[:4]

    return raw, None


def _error(protocol: str, msg: str) -> dict:
    return {
        "success": False,
        "protocol": protocol,
        "status": None,
        "observation": None,
        "updatedAt": None,
        "rawText": None,
        "error": msg,
        "_fonte": FONTE,
        "_situacao": None,
        "_screenshot": None,
    }


def _fill_by_label(page: Any, label: str, value: str) -> bool:
    patterns = [
        rf"label:has-text('{label}') input",
        rf"input[placeholder*='{label}' i]",
        rf"input[aria-label*='{label}' i]",
    ]
    for selector in patterns:
        try:
            locator = page.locator(selector).first
            if locator.count():
                locator.scroll_into_view_if_needed(timeout=1000)
                locator.click(timeout=1000)
                locator.fill(value)
                locator.evaluate(
                    """
                    (input) => {
                      input.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: input.value }));
                      input.dispatchEvent(new Event('change', { bubbles: true }));
                      input.dispatchEvent(new Event('blur', { bubbles: true }));
                    }
                    """
                )
                return True
        except Exception:
            pass

    try:
        return page.evaluate(
            """
            ({ label, value }) => {
              const norm = (s) => (s || '').normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();
              const wanted = norm(label);
              const setValue = (input) => {
                if (!input) return false;
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
                if (setter) setter.call(input, value);
                else input.value = value;
                input.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: value }));
                input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: 'Tab' }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.dispatchEvent(new Event('blur', { bubbles: true }));
                return true;
              };

              const direct = [...document.querySelectorAll('input')].find((input) => {
                const text = [input.placeholder, input.getAttribute('aria-label'), input.name, input.id, input.getAttribute('formcontrolname')].join(' ');
                return norm(text).includes(wanted);
              });
              if (setValue(direct)) return true;

              for (const el of [...document.querySelectorAll('label')]) {
                if (!norm(el.textContent).includes(wanted)) continue;
                const forInput = document.getElementById(el.getAttribute('for'));
                const containers = [el, el.parentElement, el.closest('.form-group'), el.closest('.form-row'), el.closest('.col'), el.closest('div')].filter(Boolean);
                const input = forInput || containers.map((node) => node.querySelector('input')).find(Boolean);
                if (input) {
                  input.scrollIntoView({ block: 'center', inline: 'center' });
                  return setValue(input);
                }
              }
              return false;
            }
            """,
            {"label": label, "value": value},
        )
    except Exception:
        return False


def _select_entidade(page: Any) -> None:
    try:
        selects = page.locator("select")
        for i in range(selects.count()):
            select = selects.nth(i)
            options = select.locator("option").all_inner_texts()
            match = next((opt for opt in options if "toledo" in opt.lower()), None)
            if match:
                select.select_option(label=match)
                return
    except Exception:
        pass

    try:
        page.evaluate(
            """
            () => {
              const norm = (s) => (s || '').normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();
              for (const select of document.querySelectorAll('select')) {
                const option = [...select.options].find((opt) => norm(opt.textContent).includes('municipio de toledo'));
                if (!option) continue;
                select.value = option.value;
                select.dispatchEvent(new Event('input', { bubbles: true }));
                select.dispatchEvent(new Event('change', { bubbles: true }));
                return true;
              }
              return false;
            }
            """
        )
    except Exception:
        pass


def _click_search(page: Any) -> bool:
    try:
        buscar = page.locator("#buscar").first
        if buscar.count():
            page.wait_for_function(
                """
                () => {
                  const btn = document.querySelector('#buscar');
                  return !!btn && !btn.disabled && btn.getAttribute('disabled') === null;
                }
                """,
                timeout=12000,
            )
            buscar.scroll_into_view_if_needed(timeout=1000)
            buscar.click(force=True)
            return True
    except Exception:
        pass

    for xpath in [
        "/html/body/app-root/div/div[1]/div/div[2]/main/app-protocolo-pesquisa-processos/div/div/form/div/button[2]",
        "//app-protocolo-pesquisa-processos//form//button[2]",
    ]:
        try:
            button = page.locator(f"xpath={xpath}").first
            if button.count() and button.is_visible(timeout=1000) and button.is_enabled(timeout=1000):
                button.scroll_into_view_if_needed(timeout=1000)
                button.click(force=True)
                return True
        except Exception:
            pass

    for selector in [
        "button:has-text('Pesquisar')",
        "button:has-text('Consultar')",
        "button:has-text('Buscar')",
        "a:has-text('Pesquisar')",
        "a:has-text('Consultar')",
        "a:has-text('Buscar')",
        "[ng-click*='pesquis' i]",
        "[ng-click*='consult' i]",
        "[ng-click*='buscar' i]",
        "[data-ng-click*='pesquis' i]",
        "[data-ng-click*='consult' i]",
        "[data-ng-click*='buscar' i]",
        "[title*='Pesquisar' i]",
        "[title*='Consultar' i]",
        "[aria-label*='Pesquisar' i]",
        "[aria-label*='Consultar' i]",
        "input[type='submit']",
        "button[type='submit']",
        "button.btn-primary",
        "button.btn-success",
        ".btn-primary",
        ".btn-success",
    ]:
        try:
            buttons = page.locator(selector)
            count = buttons.count()
            for i in range(count - 1, -1, -1):
                candidate = buttons.nth(i)
                if candidate.is_visible(timeout=500) and candidate.is_enabled(timeout=500):
                    candidate.scroll_into_view_if_needed(timeout=1000)
                    candidate.click(force=True)
                    return True
        except Exception:
            pass

    try:
        clicked = page.evaluate(
            """
            () => {
              const norm = (s) => (s || '').normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();
              const isVisible = (el) => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
              };
              const candidates = [...document.querySelectorAll('button,a,input,[role="button"],.btn')];
              for (const el of candidates) {
                if (!isVisible(el)) continue;
                if (el.disabled || el.getAttribute('disabled') !== null) continue;
                const text = norm([el.innerText, el.value, el.title, el.getAttribute('aria-label'), el.getAttribute('ng-click'), el.getAttribute('data-ng-click'), el.className].join(' '));
                if (!/(pesquis|consult|buscar|search)/.test(text)) continue;
                el.scrollIntoView({ block: 'center', inline: 'center' });
                el.click();
                return true;
              }
              const form = document.querySelector('form');
              if (form) {
                form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
                return true;
              }
              return false;
            }
            """
        )
        if clicked:
            return True
    except Exception:
        pass

    return False


def _clickable_summary(page: Any) -> str:
    try:
        items = page.evaluate(
            """
            () => {
              const normSpace = (s) => (s || '').replace(/\\s+/g, ' ').trim();
              return [...document.querySelectorAll('button,a,input,[role="button"],.btn')]
                .map((el) => normSpace([
                  el.tagName,
                  el.id ? `#${el.id}` : '',
                  el.disabled || el.getAttribute('disabled') !== null ? 'disabled' : 'enabled',
                  el.innerText,
                  el.value,
                  el.title,
                  el.getAttribute('aria-label'),
                  el.getAttribute('ng-click'),
                  el.getAttribute('data-ng-click'),
                  el.className
                ].filter(Boolean).join(' | ')))
                .filter(Boolean)
                .slice(0, 12);
            }
            """
        )
        return "; ".join(items)[:500]
    except Exception:
        return ""
    return False


def _map_status(text: str) -> str | None:
    upper = (text or "").upper()
    haystack = f"{upper} {upper.encode('ascii', 'ignore').decode('ascii')}"
    patterns = [
        ("CANCELADO", "CANCELADO"),
        ("ARQUIVADO", "CANCELADO"),
        ("INDEFERIDO", "REPROVADO"),
        ("REPROVADO", "REPROVADO"),
        ("DEFERIDO", "APROVADO"),
        ("APROVADO", "APROVADO"),
        ("FINALIZADO", "APROVADO"),
        ("CONCLUIDO", "APROVADO"),
        ("CONCLUÍDO", "APROVADO"),
        ("PENDENTE", "PENDENTE"),
        ("EXIGENCIA", "PENDENTE"),
        ("EXIGÊNCIA", "PENDENTE"),
        ("AGUARDANDO", "PENDENTE"),
        ("EM ANALISE", "EM ANDAMENTO"),
        ("EM ANÁLISE", "EM ANDAMENTO"),
        ("ANALISE", "EM ANDAMENTO"),
        ("ANÁLISE", "EM ANDAMENTO"),
        ("ANDAMENTO", "EM ANDAMENTO"),
        ("TRAMITANDO", "EM ANDAMENTO"),
    ]
    for needle, status in patterns:
        if needle in haystack:
            return status
    return None


def _movement_from_cells(cells: list[str]) -> dict | None:
    values = [re.sub(r"\s+", " ", cell or "").strip() for cell in cells]
    values = [value for value in values if value]
    if len(values) < 4:
        return None

    date_idx = next(
        (idx for idx, value in enumerate(values) if re.search(r"\d{2}/\d{2}/\d{4}", value)),
        None,
    )
    if date_idx is None:
        return None

    tail = values[date_idx:]
    if len(tail) < 4:
        return None

    return {
        "data": tail[0],
        "etapa": tail[1] if len(tail) > 1 else None,
        "local": tail[2] if len(tail) > 2 else None,
        "descricao": tail[3] if len(tail) > 3 else None,
        "previsao": tail[4] if len(tail) > 4 else None,
    }


def _extract_movements_from_page(page: Any) -> list[dict]:
    try:
        rows = page.evaluate(
            """
            () => {
              const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
              const result = [];
              const selectors = [
                '.dx-datagrid-rowsview tr.dx-data-row',
                '.dx-datagrid-rowsview .dx-row.dx-data-row',
                'tr.dx-data-row',
                '.dx-data-row'
              ];
              const rows = [...document.querySelectorAll(selectors.join(','))];
              for (const row of rows) {
                const cells = [...row.querySelectorAll('[role="gridcell"], td')].map((cell) => ({
                  col: Number(cell.getAttribute('aria-colindex') || '0'),
                  text: norm(cell.textContent || cell.innerText || '')
                }));
                result.push(cells);
              }
              return result;
            }
            """
        )
        movements: list[dict] = []
        for row in rows or []:
            by_col = {
                int(cell.get("col") or 0): cell.get("text") or ""
                for cell in row
                if cell.get("text")
            }
            if by_col:
                movement = {
                    "data": by_col.get(3),
                    "etapa": by_col.get(4),
                    "local": by_col.get(5),
                    "descricao": by_col.get(6),
                    "previsao": by_col.get(7),
                }
                if movement.get("data") and movement.get("descricao"):
                    movements.append(movement)
                    continue

            movement = _movement_from_cells([cell.get("text") or "" for cell in row])
            if movement:
                movements.append(movement)
        return movements
    except Exception:
        return []


def _extract_movements_from_html(html: str) -> list[dict]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    soup = BeautifulSoup(html or "", "html.parser")
    movements: list[dict] = []
    for row in soup.select(".dx-datagrid-rowsview tr.dx-data-row"):
        cells = [cell.get_text(" ", strip=True) for cell in row.select("td[role='gridcell']")]
        movement = _movement_from_cells(cells)
        if movement:
            movements.append(movement)
    return movements


def _parse_result(
    html: str,
    body_text: str,
    protocol: str,
    movements: list[dict] | None = None,
) -> tuple[str | None, str, str | None, str | None]:
    movements = movements or _extract_movements_from_html(html)
    if movements:
        latest = movements[0]
        status_text = " ".join(str(latest.get(key) or "") for key in ("etapa", "local", "descricao"))
        status = _map_status(status_text) or "EM ANDAMENTO"
        parts = [
            f"Ultima movimentacao em {latest.get('data')}",
            f"Etapa: {latest.get('etapa')}" if latest.get("etapa") else None,
            f"Local: {latest.get('local')}" if latest.get("local") else None,
            f"Descricao: {latest.get('descricao')}" if latest.get("descricao") else None,
            f"Previsao: {latest.get('previsao')}" if latest.get("previsao") else None,
        ]
        return status, "; ".join(part for part in parts if part) + ".", latest.get("data"), None

    clean_text = re.sub(r"\s+", " ", body_text or "").strip()
    if re.search(r"nenhum\s+registro|nao\s+encontrado|não\s+encontrado|sem\s+resultado|inexistente", clean_text, re.I):
        return None, f"Processo {protocol} nao localizado no Equiplano Toledo.", None, "NAO_ENCONTRADO"

    return (
        None,
        "Consulta executada, mas nenhuma movimentacao real foi extraida da grade do Equiplano.",
        None,
        "SEM_MOVIMENTACAO_EXTRAIDA",
    )


def _sync_query(protocol: str, processo: str, exercicio: str) -> dict:
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
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PWTimeout:
            pass

        _fill_by_label(page, "Processo", processo)
        _fill_by_label(page, "Exercicio", exercicio)
        _fill_by_label(page, "Exercício", exercicio)
        _fill_by_label(page, "CPF/CNPJ", CNPJ_CARMEL)
        _select_entidade(page)
        page.wait_for_timeout(800)

        if not _click_search(page):
            summary = _clickable_summary(page)
            detail = f" Elementos clicaveis: {summary}" if summary else ""
            raise RuntimeError(f"Botao de pesquisa nao localizado.{detail}")

        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PWTimeout:
            pass
        page.wait_for_timeout(2500)
        try:
            page.locator(".dx-datagrid-rowsview tr.dx-data-row").first.wait_for(timeout=10000)
        except PWTimeout:
            pass

        screenshot = page.screenshot(full_page=True)
        html = page.content()
        body_text = page.locator("body").inner_text(timeout=5000)
        movements = _extract_movements_from_page(page)
        browser.close()

    status, observation, updated_at, situacao = _parse_result(html, body_text, protocol, movements)
    raw_text = html[:7000] if html else None
    if movements:
        raw_text = f"MOVIMENTACOES_EQUIPLANO={json.dumps(movements, ensure_ascii=False)}\n{raw_text or ''}"[:8000]

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
        "_screenshot": base64.b64encode(screenshot).decode(),
    }


def query_protocol(p: dict) -> dict:
    protocol = (p.get("protocolo") or "").strip()
    if not protocol:
        return _error(protocol, "Numero do protocolo nao informado - consulta nao realizada.")

    processo, exercicio = _split_process_exercise(protocol, p.get("data_abertura"))
    if not processo:
        return _error(protocol, "Processo nao identificado a partir do protocolo cadastrado.")
    if not exercicio:
        return _error(protocol, "Exercicio nao identificado. Informe protocolo no formato numero/ano ou data de abertura.")

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_sync_query, protocol, processo, exercicio)
            return future.result(timeout=120)
    except Exception as exc:
        return {
            "success": False,
            "protocol": protocol,
            "status": None,
            "observation": None,
            "updatedAt": None,
            "rawText": None,
            "error": f"Erro na consulta ao Equiplano Toledo: {str(exc)[:300]}",
            "_fonte": FONTE,
            "_situacao": None,
            "_screenshot": None,
        }
