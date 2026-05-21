"""
Scraper real para consulta de protocolo no ePROTOCOLO — Corpo de Bombeiros do Paraná (CBPR).

O portal ePROTOCOLO (Governo do PR) é o canal de consulta pública dos protocolos do CBPR.

Fluxo:
- Abre consultarProtocoloDigital.do?action=pesquisar
- Preenche #numeroProtocolo e clica em #btnPesquisar
- Extrai Local de Envio, Onde está, Motivo, Enviado em e dias em trâmite
"""

from __future__ import annotations

import base64
import concurrent.futures
import json
import re
from typing import Any


URL = "https://www.eprotocolo.pr.gov.br/spiweb/consultarProtocoloDigital.do?action=pesquisar"
FONTE = "CBPR — Corpo de Bombeiros do Paraná (ePROTOCOLO PR)"


def _only_digits(value: str) -> str:
    return re.sub(r"\D+", "", value or "")


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


def _map_status(motivo: str) -> str | None:
    upper = (motivo or "").upper()
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
        ("SOBRESTADO", "PENDENTE"),
        ("EM ANALISE", "EM ANDAMENTO"),
        ("EM ANÁLISE", "EM ANDAMENTO"),
        ("ANALISE", "EM ANDAMENTO"),
        ("ANÁLISE", "EM ANDAMENTO"),
        ("ANDAMENTO", "EM ANDAMENTO"),
        ("TRAMITANDO", "EM ANDAMENTO"),
        ("TRÂMITE", "EM ANDAMENTO"),
        ("TRAMITE", "EM ANDAMENTO"),
    ]
    for needle, status in patterns:
        if needle in haystack:
            return status
    return "EM ANDAMENTO" if motivo else None


def _parse_enviado_em(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"(\d{2}/\d{2}/\d{4})", value)
    return match.group(1) if match else None


def _extract_fields_from_page(page: Any) -> dict[str, str]:
    try:
        data = page.evaluate(
            """
            () => {
              const norm = (s) => (s || '').replace(/\\s+/g, ' ').trim();
              const fields = {};

              const addPair = (label, value) => {
                if (!label || !value) return;
                fields[label] = value;
              };

              for (const row of document.querySelectorAll('.fieldset .row, .mb-2 .fieldset .row')) {
                const labels = [...row.querySelectorAll('label')];
                const values = [...row.querySelectorAll('.fw-medium')];
                if (!labels.length || !values.length) continue;

                if (labels.length === values.length) {
                  labels.forEach((label, idx) => addPair(norm(label.textContent), norm(values[idx].textContent)));
                  continue;
                }

                let valueIdx = 0;
                for (const label of labels) {
                  const text = norm(label.textContent);
                  if (!text || valueIdx >= values.length) continue;
                  addPair(text, norm(values[valueIdx].textContent));
                  valueIdx += 1;
                }
              }

              if (Object.keys(fields).length) return fields;

              for (const label of document.querySelectorAll('label')) {
                const text = norm(label.textContent);
                if (!text) continue;
                const row = label.closest('.row');
                const valueNode = row
                  ? [...row.querySelectorAll('.fw-medium, .col-md-3.fw-medium, .col-md-4.fw-medium')].find((node) => node !== label)
                  : null;
                if (valueNode) addPair(text.replace(/:$/, ''), norm(valueNode.textContent));
              }
              return fields;
            }
            """
        )
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _extract_fields_from_html(html: str) -> dict[str, str]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {}

    soup = BeautifulSoup(html or "", "html.parser")
    fields: dict[str, str] = {}

    for row in soup.select(".fieldset .row"):
        labels = [label.get_text(" ", strip=True) for label in row.select("label")]
        values = [node.get_text(" ", strip=True) for node in row.select(".fw-medium")]
        if not labels or not values:
            continue
        if len(labels) == len(values):
            for label, value in zip(labels, values):
                if label and value:
                    fields[label.rstrip(":")] = value
            continue
        for idx, label in enumerate(labels):
            if idx < len(values) and label:
                fields[label.rstrip(":")] = values[idx]

    return fields


def _build_observation(protocol: str, fields: dict[str, str]) -> str:
    parts = [
        f"Protocolo {protocol} consultado no ePROTOCOLO PR (Corpo de Bombeiros do Paraná).",
        f"Local de Envio: {fields['Local de Envio']}" if fields.get("Local de Envio") else None,
        f"Onde está: {fields['Onde está']}" if fields.get("Onde está") else None,
        f"Motivo: {fields['Motivo']}" if fields.get("Motivo") else None,
        f"Enviado em: {fields['Enviado em']}" if fields.get("Enviado em") else None,
        f"Dias em Trâmite: {fields['Dias em Trâmite']}" if fields.get("Dias em Trâmite") else None,
        f"Dias Sobrestado: {fields['Dias Sobrestado']}" if fields.get("Dias Sobrestado") else None,
        f"Dias Arquivo Corrente: {fields['Dias Arquivo Corrente']}" if fields.get("Dias Arquivo Corrente") else None,
    ]
    return " ".join(part for part in parts if part)


def _parse_result(
    html: str,
    body_text: str,
    protocol: str,
    fields: dict[str, str],
) -> tuple[str | None, str, str | None, str | None]:
    clean_text = re.sub(r"\s+", " ", body_text or "").strip()
    not_found = re.search(
        r"nao\s+encontrado|não\s+encontrado|nenhum\s+registro|sem\s+resultado|inexistente|protocolo\s+inexistente"
        r"|digito\s+verificador|dígito\s+verificador|protocolo\s+invalido|protocolo\s+inválido",
        clean_text,
        re.I,
    )
    has_details = any(fields.get(key) for key in ("Motivo", "Local de Envio", "Onde está", "Enviado em"))

    if not_found and not has_details:
        msg_match = re.search(
            r"(d[ií]gito verificador[^.]*|protocolo[^.]*inv[aá]lido[^.]*|n[aã]o encontrado[^.]*)",
            clean_text,
            re.I,
        )
        detalhe = msg_match.group(1).strip() if msg_match else "nao localizado"
        return None, f"Protocolo {protocol} — {detalhe} (ePROTOCOLO PR).", None, "NAO_ENCONTRADO"

    if not has_details:
        return (
            None,
            f"Consulta ao ePROTOCOLO PR executada, mas os dados do protocolo {protocol} nao foram extraidos.",
            None,
            "SEM_DADOS_EXTRAIDOS",
        )

    motivo = fields.get("Motivo") or ""
    status = _map_status(motivo)
    observation = _build_observation(protocol, fields)
    updated_at = _parse_enviado_em(fields.get("Enviado em"))
    return status, observation, updated_at, None


def _fill_protocol(page: Any, numero: str) -> None:
    input_el = page.locator("#numeroProtocolo").first
    input_el.wait_for(state="visible", timeout=15000)
    input_el.click()
    input_el.fill(numero)
    page.evaluate(
        """
        (value) => {
          const input = document.querySelector('#numeroProtocolo');
          if (!input) return;
          if (typeof MascaraProtocolo === 'function') {
            MascaraProtocolo(input, { key: '0' });
          }
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.dispatchEvent(new Event('keyup', { bubbles: true }));
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
        """,
        numero,
    )


def _click_search(page: Any) -> bool:
    for selector in ["#btnPesquisar", "button#btnPesquisar", "button:has-text('Pesquisar')"]:
        try:
            button = page.locator(selector).first
            if button.count() and button.is_visible(timeout=2000):
                button.scroll_into_view_if_needed(timeout=1000)
                button.click(force=True)
                return True
        except Exception:
            pass

    try:
        return page.evaluate(
            """
            () => {
              const btn = document.querySelector('#btnPesquisar');
              if (btn) {
                btn.click();
                return true;
              }
              if (typeof pesquisar === 'function') {
                pesquisar();
                return true;
              }
              return false;
            }
            """
        )
    except Exception:
        return False


def _wait_for_result(page: Any) -> None:
    from playwright.sync_api import TimeoutError as PWTimeout

    try:
        page.wait_for_function(
            """
            () => {
              const hasFieldset = !!document.querySelector('.fieldset .fw-medium');
              const body = (document.body?.innerText || '').toLowerCase();
              const notFound = /não encontrado|nao encontrado|inexistente/.test(body);
              return hasFieldset || notFound;
            }
            """,
            timeout=20000,
        )
    except PWTimeout:
        pass

    try:
        page.wait_for_load_state("networkidle", timeout=12000)
    except PWTimeout:
        pass
    page.wait_for_timeout(1500)


def _sync_query(protocol: str, numero_protocolo: str, url: str) -> dict:
    try:
        from playwright.sync_api import TimeoutError as PWTimeout
        from playwright.sync_api import sync_playwright
    except ImportError:
        return _error(protocol, "Playwright nao instalado.")

    target_url = (url or "").strip() or URL

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        )
        page = context.new_page()
        page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PWTimeout:
            pass

        _fill_protocol(page, numero_protocolo)

        if not _click_search(page):
            browser.close()
            return _error(protocol, "Botao Pesquisar nao localizado no ePROTOCOLO PR.")

        _wait_for_result(page)

        screenshot = page.screenshot(full_page=True)
        html = page.content()
        body_text = page.locator("body").inner_text(timeout=5000)
        fields = _extract_fields_from_page(page)
        if not fields:
            fields = _extract_fields_from_html(html)
        browser.close()

    status, observation, updated_at, situacao = _parse_result(html, body_text, protocol, fields)
    raw_payload = {"campos": fields, "protocolo_consultado": numero_protocolo}
    raw_text = f"EPROTOCOLO_PR={json.dumps(raw_payload, ensure_ascii=False)}\n{html[:6500] if html else ''}"[:8000]

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
            "_screenshot": base64.b64encode(screenshot).decode(),
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
            "_screenshot": base64.b64encode(screenshot).decode(),
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
        "_screenshot": base64.b64encode(screenshot).decode(),
    }


def query(protocol: str, orgao: str, url: str) -> dict:
    return query_protocol({"protocolo": protocol, "url_consulta": url, "orgao_site_consultado": orgao})


def query_protocol(p: dict) -> dict:
    protocol = (p.get("protocolo") or "").strip()
    if not protocol:
        return _error(protocol, "Numero do protocolo nao informado - consulta nao realizada.")

    numero = _only_digits(protocol)[:12]
    if not numero:
        return _error(protocol, "Numero do protocolo invalido para consulta no ePROTOCOLO PR.")

    url = (p.get("url_consulta") or "").strip()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_sync_query, protocol, numero, url)
            return future.result(timeout=120)
    except Exception as exc:
        return _error(protocol, f"Erro na consulta ao ePROTOCOLO PR: {str(exc)[:300]}")
