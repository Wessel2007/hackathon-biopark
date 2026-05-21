from datetime import datetime, timezone, timedelta
import random
import re
import json
import base64
import unicodedata
import asyncio
import concurrent.futures

from app.supabase_client import SupabaseClient
from app.services.email_service import enviar_alerta


# ---------------------------------------------------------------------------
# Mock simulation (fallback para órgãos sem scraper real)
# ---------------------------------------------------------------------------

_ORGAN_STATUSES: dict[str, list[str]] = {
    "prefeitura": ["EM ANÁLISE", "APROVADO", "AGUARDANDO DOCUMENTAÇÃO"],
    "copel":      ["EM ANÁLISE", "AGUARDANDO VISTORIA", "APROVADO"],
    "cartorio":   ["EM ANÁLISE", "REGISTRADO", "CANCELADO"],
}

_ORGAN_OBSERVATIONS: dict[str, dict[str, str]] = {
    "prefeitura": {
        "EM ANÁLISE":              "Processo em análise técnica. Aguardando parecer da equipe responsável.",
        "APROVADO":                "Licença aprovada. Documentação disponível para retirada no protocolo.",
        "AGUARDANDO DOCUMENTAÇÃO": "Processo suspenso. Necessário protocolar documentação complementar indicada no ofício.",
    },
    "copel": {
        "EM ANÁLISE":         "Solicitação em análise pelo setor técnico da distribuidora.",
        "AGUARDANDO VISTORIA":"Aguardando agendamento de vistoria presencial no local da obra.",
        "APROVADO":           "Conexão aprovada. Entrar em contato para agendamento da ligação.",
    },
    "cartorio": {
        "EM ANÁLISE": "Documentação em análise pelo registrador.",
        "REGISTRADO": "Registro efetivado. Certidão disponível para retirada.",
        "CANCELADO":  "Pedido cancelado a pedido do requerente ou por ausência de requisitos.",
    },
}


def _normalize(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii").lower()


def _organ_key(orgao: str) -> str:
    normalized = _normalize(orgao)
    for key in _ORGAN_STATUSES:
        if key in normalized:
            return key
    return "outros"


def _mock_query(p: dict) -> dict:
    protocolo = (p.get("protocolo") or "").strip()
    orgao = (p.get("orgao_site_consultado") or "").strip()

    if not protocolo or not orgao:
        return {
            "status_consultado":  None,
            "situacao_consultada": None,
            "observacao":         None,
            "texto_bruto":        None,
            "screenshot_base64":  None,
            "data_movimentacao":  None,
            "fonte_consulta":     f"SIMULADO: {orgao}" if orgao else "SIMULADO",
            "erro": "Protocolo ou órgão não informado — consulta não realizada.",
        }

    key = _organ_key(orgao)
    days_ago = random.randint(0, 45)
    data_mov = (datetime.now() - timedelta(days=days_ago)).strftime("%d/%m/%Y")

    if key == "outros":
        status = random.choice(["CONSULTADO", "NÃO ENCONTRADO"])
        if status == "NÃO ENCONTRADO":
            return {
                "status_consultado":  None,
                "situacao_consultada": "NAO_ENCONTRADO",
                "observacao":  f"Protocolo {protocolo} não localizado no sistema de {orgao}.",
                "texto_bruto": None,
                "screenshot_base64": None,
                "data_movimentacao": data_mov,
                "fonte_consulta": f"SIMULADO: {orgao}",
                "erro": None,
            }
        obs = f"Protocolo {protocolo} localizado no sistema de {orgao}. Consulta realizada com sucesso."
    else:
        status = random.choice(_ORGAN_STATUSES[key])
        template = (_ORGAN_OBSERVATIONS.get(key) or {}).get(status, "")
        obs = f"Protocolo {protocolo} — {template}" if template else f"Protocolo {protocolo}: {status}."

    return {
        "status_consultado":   status,
        "situacao_consultada": None,
        "observacao":          obs,
        "texto_bruto":         None,
        "screenshot_base64":   None,
        "data_movimentacao":   data_mov,
        "fonte_consulta":      f"SIMULADO: {orgao}",
        "erro":                None,
    }


# ---------------------------------------------------------------------------
# Scraper real — Cartório PR (Toledo)
# ---------------------------------------------------------------------------

_CARTORIOS_PR_URL = "https://www.cartoriospr.com.br/eandamento/index.php?token="


def _is_cartorios_pr_query(p: dict) -> bool:
    """Retorna True apenas para protocolos do Cartório Imóveis (cartoriospr.com.br)."""
    orgao = _normalize(p.get("orgao_site_consultado") or "")
    url   = (p.get("url_consulta") or "").lower()
    # Aceita variações: "Cartório Imóveis", "Cartório de Imóveis", "1° Ofício de Imóveis", etc.
    # _normalize remove acentos: "imóveis" → "imoveis", "imóvel" → "imovel"
    return (
        "imoveis" in orgao
        or "imovel" in orgao
        or "cartoriospr" in url
        or "eandamento" in url
    )


# Scraper real - Equiplano Toledo (CARMEL)
def _is_equiplano_toledo_carmel_query(p: dict) -> bool:
    """Retorna True para processos da CARMEL no Equiplano do Municipio de Toledo."""
    url = (p.get("url_consulta") or "").lower()
    orgao = _normalize(p.get("orgao_site_consultado") or "")
    projeto = _normalize(p.get("projeto") or "")
    atividade = _normalize(p.get("atividade") or "")

    if "equiplano.toledo.pr.gov.br" in url or "stpprocessos" in url:
        return True

    return (
        "carmel" in projeto
        and ("toledo" in orgao or "toledo" in atividade)
        and ("municipio" in orgao or "prefeitura" in orgao or "equiplano" in orgao)
    )


# Mapeamento dos status do cartório para os status internos do sistema
_CARTORIO_STATUS_MAP: dict[str, str] = {
    "REGISTRADO":   "APROVADO",
    "APROVADO":     "APROVADO",
    "EM ANÁLISE":   "EM ANDAMENTO",
    "EM ANDAMENTO": "EM ANDAMENTO",
    "PRENOTADO":    "EM ANDAMENTO",
    "EXAMINADO":    "EM ANDAMENTO",
    "QUALIFICADO":  "EM ANDAMENTO",
    "AGUARDANDO":   "PENDENTE",
    "DEVOLVIDO":    "PENDENTE",
    "PENDENTE":     "PENDENTE",
    "CANCELADO":    "CANCELADO",
}


def _mapear_status_sistema(status_cartorio: str | None) -> str | None:
    """Converte o status retornado pelo site do cartório para o status interno."""
    if not status_cartorio:
        return None
    upper = status_cartorio.strip().upper()
    norm  = _normalize(upper)
    # Busca exata (com acento) primeiro
    if upper in _CARTORIO_STATUS_MAP:
        return _CARTORIO_STATUS_MAP[upper]
    # Busca normalizada (sem acento) e parcial
    norm_map = {_normalize(k): v for k, v in _CARTORIO_STATUS_MAP.items()}
    if norm in norm_map:
        return norm_map[norm]
    for key_norm, val in norm_map.items():
        if key_norm in norm:
            return val
    return upper  # mantém o original se não mapeado


def _parse_cartorio_result(html: str, protocolo: str) -> tuple:
    """Retorna (status, observacao, data_movimentacao) extraídos do HTML de resultado."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    body_text = soup.get_text(" ", strip=True)

    # Verificar protocolo não encontrado (inclui mensagem específica do site)
    if re.search(
        r"número digitado não foi encontrado|não\s+encontrado|não\s+localizado"
        r"|nenhum\s+resultado|sem\s+resultado|protocolo.*não.*exist",
        body_text, re.I
    ):
        return None, f"Protocolo {protocolo} não localizado no cartório.", None

    status = None
    obs_parts = []
    data_mov = None

    _STATUS_KEYWORDS = [
        "REGISTRADO", "EM ANÁLISE", "EM ANDAMENTO", "EXAMINADO",
        "CANCELADO", "AGUARDANDO", "APROVADO", "PENDENTE", "DEVOLVIDO",
        "QUALIFICADO", "PRENOTADO",
    ]

    # Buscar em tabelas
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in row.find_all(["td", "th"])]
            for i, cell in enumerate(cells):
                cell_up = cell.upper()
                for kw in _STATUS_KEYWORDS:
                    if kw in cell_up:
                        status = kw
                        # células adjacentes como observação
                        adj = [c for j, c in enumerate(cells) if j != i and c]
                        if adj:
                            obs_parts.append(" | ".join(adj))
                        break
                date_m = re.search(r"\d{2}/\d{2}/\d{4}", cell)
                if date_m and not data_mov:
                    data_mov = date_m.group()

    # Fallback: buscar no texto completo
    if not status:
        for kw in _STATUS_KEYWORDS:
            if kw in body_text.upper():
                status = kw
                break

    if not data_mov:
        date_m = re.search(r"\d{2}/\d{2}/\d{4}", body_text)
        if date_m:
            data_mov = date_m.group()

    obs = " | ".join(obs_parts) if obs_parts else (
        f"Protocolo {protocolo}: {status}." if status else
        f"Protocolo {protocolo} consultado. Verifique o screenshot para detalhes."
    )

    return status, obs, data_mov


def _sync_playwright_query(protocolo: str, orgao: str, url_salva: str) -> dict:
    """Lógica do scraper usando sync_playwright (seguro em thread, sem asyncio)."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        return {"erro": "Playwright não instalado.", "screenshot_base64": None}

    oficios = "2" if "2" in orgao else "1"
    serventia_label = f"Toledo - {oficios}º Ofício"

    nav_url = url_salva if (url_salva and "cartoriospr" in url_salva) else f"{_CARTORIOS_PR_URL}{protocolo}"

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        # ── Navegação ──────────────────────────────────────────────────────
        page.goto(nav_url, wait_until="domcontentloaded", timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except PWTimeout:
            pass

        # Se cair no formulário (tem <select>), preencher manualmente
        selects = page.locator("select")
        if selects.count() > 0:
            # 1. Serventia
            try:
                selects.first.select_option(label=serventia_label)
            except Exception:
                try:
                    selects.first.select_option(label=re.compile(rf"Toledo.*{oficios}", re.I))
                except Exception:
                    pass

            # 2. Tipo: Protocolo de Registro/Averbações (2° radio)
            radios = page.locator("input[type='radio']")
            if radios.count() > 1:
                try:
                    radios.nth(1).check(force=True)
                except Exception:
                    pass

            # 3. Número do protocolo
            for sel in ["input[type='number']", "input[type='text']"]:
                inputs = page.locator(sel)
                if inputs.count() > 0:
                    try:
                        inputs.first.fill(protocolo)
                        break
                    except Exception:
                        pass

            # 4. Checkbox de termos
            checkboxes = page.locator("input[type='checkbox']")
            for i in range(checkboxes.count()):
                try:
                    if not checkboxes.nth(i).is_checked():
                        checkboxes.nth(i).check(force=True)
                except Exception:
                    pass

            # 5. Clicar em Consultar
            clicked = False
            for btn_sel in ["button:has-text('Consultar')", "input[type='submit']", "button[type='submit']", "button"]:
                btns = page.locator(btn_sel)
                if btns.count() > 0:
                    try:
                        btns.last.click()
                        clicked = True
                        break
                    except Exception:
                        continue
            if not clicked:
                try:
                    page.locator("form").first.evaluate("f => f.submit()")
                except Exception:
                    pass

            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except PWTimeout:
                pass
            page.wait_for_timeout(1500)
        else:
            page.wait_for_timeout(1000)

        # ── Screenshot e parse ─────────────────────────────────────────────
        screenshot_bytes = page.screenshot(full_page=True)
        html = page.content()
        browser.close()

    screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
    status, obs, data_mov = _parse_cartorio_result(html, protocolo)

    return {
        "status_consultado":  status,
        "situacao_consultada": None,
        "observacao":         obs,
        "texto_bruto":        html[:8000] if html else None,
        "screenshot_base64":  screenshot_b64,
        "data_movimentacao":  data_mov,
        "fonte_consulta":     f"CARTÓRIO PR — {serventia_label}",
        "erro":               None,
    }


def _query_cartorios_pr_toledo(p: dict) -> dict:
    protocolo = (p.get("protocolo") or "").strip()
    orgao     = (p.get("orgao_site_consultado") or "").strip()
    url_salva = (p.get("url_consulta") or "").strip()

    if not protocolo:
        return {
            "status_consultado":  None,
            "situacao_consultada": None,
            "observacao":         None,
            "texto_bruto":        None,
            "screenshot_base64":  None,
            "data_movimentacao":  None,
            "fonte_consulta":     _CARTORIOS_PR_URL,
            "erro": "Número do protocolo não informado — consulta não realizada.",
        }

    try:
        # Executa em thread dedicada para não bloquear o event loop do FastAPI/uvicorn
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _sync_playwright_query, protocolo, orgao, url_salva,
            )
            return future.result(timeout=90)
    except Exception as exc:
        return {
            "status_consultado":  None,
            "situacao_consultada": None,
            "observacao":         None,
            "texto_bruto":        None,
            "screenshot_base64":  None,
            "data_movimentacao":  None,
            "fonte_consulta":     _CARTORIOS_PR_URL,
            "erro":               f"Erro na consulta ao cartório: {str(exc)[:300]}",
        }


def _query_source(p: dict) -> dict:
    if _is_cartorios_pr_query(p):
        return _query_cartorios_pr_toledo(p)
    if _is_equiplano_toledo_carmel_query(p):
        from app.services.scrapers.dispatcher import _to_internal
        from app.services.scrapers.equiplano_toledo import query_protocol

        return _to_internal(query_protocol(p))
    from app.services.scrapers.dispatcher import check_protocol_status
    return check_protocol_status(p)


# ---------------------------------------------------------------------------
# Detecção de mudanças
# ---------------------------------------------------------------------------

def _build_mudancas(ultimo: dict | None, resultado: dict, protocolo_num: str) -> list[str]:
    mudancas: list[str] = []
    num = protocolo_num

    if resultado.get("erro"):
        if not (ultimo or {}).get("erro"):
            mudancas.append(f"Protocolo {num}: consulta retornou erro")
        return mudancas

    if ultimo and ultimo.get("erro"):
        mudancas.append(f"Protocolo {num}: consulta voltou a responder com sucesso")

    not_found_now    = resultado.get("situacao_consultada") == "NAO_ENCONTRADO"
    not_found_before = (ultimo or {}).get("situacao_consultada") == "NAO_ENCONTRADO"

    if not_found_now and not not_found_before:
        mudancas.append(f"Protocolo {num} deixou de ser encontrado no sistema")
        return mudancas
    if not_found_now:
        return mudancas

    if not ultimo:
        return mudancas

    status_ant = ultimo.get("status_consultado")
    status_nov = resultado.get("status_consultado")
    if status_ant and status_nov and status_ant != status_nov:
        mudancas.append(f'Protocolo {num} mudou de "{status_ant}" para "{status_nov}"')

    obs_ant = (ultimo.get("observacao") or "").strip()
    obs_nov = (resultado.get("observacao") or "").strip()
    if obs_nov and not obs_ant:
        mudancas.append(f"Protocolo {num}: nova observação registrada")
    elif obs_nov and obs_ant and obs_nov != obs_ant:
        mudancas.append(f"Protocolo {num}: observação foi atualizada")

    data_ant = (ultimo.get("data_movimentacao") or "").strip()
    data_nov = (resultado.get("data_movimentacao") or "").strip()
    if data_nov and not data_ant:
        mudancas.append(f"Protocolo {num}: nova data de movimentação registrada ({data_nov})")
    elif data_nov and data_ant and data_nov != data_ant:
        mudancas.append(f"Protocolo {num}: data de movimentação mudou de {data_ant} para {data_nov}")

    return mudancas


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def run_single_query(protocol_id: int, sb: SupabaseClient, user_email: str = "") -> dict:
    result = (
        sb.table("protocols")
        .select("*, query_history(*)")
        .eq("id", protocol_id)
        .maybe_single()
        .execute()
    )
    p = result.data
    if not p:
        return {"erro": "Protocolo não encontrado"}

    resultado = _query_source(p)

    historico = sorted(
        p.get("query_history") or [],
        key=lambda x: x.get("data_consulta") or "",
    )
    ultimo = historico[-1] if historico else None

    protocolo_num = p.get("protocolo", str(protocol_id))
    mudancas      = _build_mudancas(ultimo, resultado, protocolo_num)
    houve_mudanca = bool(mudancas)

    status_anterior = (ultimo.get("status_consultado") if ultimo else None) or p.get("status")
    status_novo     = resultado.get("status_consultado")

    if houve_mudanca:
        enviar_alerta(p, mudancas, user_email)

    now = datetime.now(timezone.utc).isoformat()

    insert_result = sb.table("query_history").insert({
        "protocol_id":        protocol_id,
        "status_consultado":  resultado["status_consultado"],
        "situacao_consultada": resultado.get("situacao_consultada"),
        "observacao":         resultado["observacao"],
        "texto_bruto":        resultado.get("texto_bruto"),
        "houve_mudanca":      houve_mudanca,
        "erro":               resultado["erro"],
        "data_consulta":      now,
        "data_movimentacao":  resultado.get("data_movimentacao"),
        "mudancas_detectadas": json.dumps(mudancas, ensure_ascii=False) if mudancas else None,
        "fonte_consulta":     resultado.get("fonte_consulta"),
        "status_anterior":    status_anterior,
        "screenshot_base64":  resultado.get("screenshot_base64"),
    }).execute()

    # Recuperar o ID do registro inserido
    history_id = None
    if insert_result.data:
        rows = insert_result.data if isinstance(insert_result.data, list) else [insert_result.data]
        if rows:
            history_id = rows[0].get("id")

    update_payload: dict = {
        "ultima_consulta":     now,
        "observacao_consulta": resultado["observacao"],
    }
    if resultado["status_consultado"] and not resultado["erro"]:
        # Para o Cartório Imóveis mapeia para o status interno; outros já vêm corretos
        status_sistema = _mapear_status_sistema(resultado["status_consultado"])
        if status_sistema:
            update_payload["status"] = status_sistema
    sb.table("protocols").update(update_payload).eq("id", protocol_id).execute()

    tem_evidencia = bool(resultado.get("screenshot_base64"))

    return {
        "protocolo":         p["protocolo"],
        "resultado": {
            **{k: v for k, v in resultado.items() if k != "screenshot_base64"},
            "data_hora_consulta": now,
        },
        "houve_mudanca":      houve_mudanca,
        "mudancas_detectadas": mudancas,
        "status_anterior":    status_anterior,
        "status_novo":        status_novo,
        "erro":               resultado.get("erro"),
        "history_id":         history_id,
        "tem_evidencia":      tem_evidencia,
    }


def run_all_queries(sb: SupabaseClient, user_email: str = "") -> None:
    protocols = sb.table("protocols").select("id").eq("ativo", True).execute().data
    for p in (protocols or []):
        run_single_query(p["id"], sb, user_email)
