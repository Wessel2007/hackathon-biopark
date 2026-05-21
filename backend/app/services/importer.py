import re
from datetime import datetime, date

import openpyxl
import pandas as pd
from supabase import Client

SKIP_SHEETS = {"Configuração"}

STATUS_MAP = {
    "CANC": "CANCELADO",
    "ANÁL": "EM ANDAMENTO",
    "APRO": "APROVADO",
}

# Separadores aceitos entre Projeto e Protocolo, em ordem de prioridade.
# Apenas variantes com espaço ou em-dash explícito — evita falsos positivos
# com hifens dentro do número do protocolo (ex: "SEI-12345").
_SEPS = [" – ", " - ", " / ", "– "]

_CAMPOS_OBRIGATORIOS = ("status", "projeto", "protocolo", "atividade")
_CAMPOS_TEXTO = ("orgao_site_consultado", "atribuido_a", "situacao", "url_consulta", "observacao_consulta")
_CAMPOS_DATA = ("data_abertura", "data_finalizacao")


# ---------------------------------------------------------------------------
# Helpers de transformação
# ---------------------------------------------------------------------------

def _normaliza_status(s):
    if not s:
        return ""
    s = str(s).strip().upper()
    return STATUS_MAP.get(s, s)


def _limpa_texto(v):
    if v is None:
        return None
    s = str(v).strip().replace("\n", " ").replace("\r", " ")
    s = re.sub(r" {2,}", " ", s)
    return s if s else None


def _formata_data(v):
    """Converte qualquer valor de data para ISO string ou None — nunca lança exceção."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    s = str(v).strip()
    if not s or s.lower() in ("nan", "none", "nat"):
        return None
    try:
        return pd.to_datetime(s).date().isoformat()
    except Exception:
        return None


def _inferir_ativo(status, data_finalizacao):
    if str(status or "").upper() == "CANCELADO":
        return False
    if data_finalizacao:
        return False
    return True


def _projeto_do_nome(nome_aba):
    partes = nome_aba.split(" - ", 1)
    return partes[-1].strip() if len(partes) > 1 else nome_aba.strip()


def _safe_get(row, idx, default=None):
    if idx is None:
        return default
    try:
        return row[idx]
    except (IndexError, TypeError):
        return default


def _extrai_projeto_protocolo(col_b_val, col_b_header, nome_aba):
    """
    Separa o campo combinado "Projeto + Protocolo".
    Aceita os separadores: ' – ', ' - ', ' / ', '– ' (em ordem).
    Se nenhum separador for encontrado, usa o nome da aba como projeto.
    """
    col_b_str = str(col_b_header or "").lower()
    if "projeto" not in col_b_str:
        return _projeto_do_nome(nome_aba), _limpa_texto(col_b_val) or ""

    texto = _limpa_texto(col_b_val) or ""
    for sep in _SEPS:
        if sep in texto:
            partes = texto.split(sep, 1)
            projeto, protocolo = partes[0].strip(), partes[1].strip()
            if projeto and protocolo:
                return projeto, protocolo

    # Sem separador reconhecível — projeto do nome da aba, tudo vira protocolo
    return _projeto_do_nome(nome_aba), texto


def _revalidar_payload(reg: dict):
    """
    Revalida e sanitiza um registro recebido do frontend antes de inserir.
    Garante que campos obrigatórios existem, datas são válidas e tipos estão corretos.
    Retorna (payload_limpo, msg_erro). Se msg_erro não for None, a linha deve ser ignorada.
    """
    payload = {}

    for campo in _CAMPOS_OBRIGATORIOS:
        val = str(reg.get(campo, "") or "").strip()
        if not val:
            return None, f"Campo obrigatório ausente: {campo}"
        payload[campo] = val

    for campo in _CAMPOS_TEXTO:
        val = str(reg.get(campo, "") or "").strip()
        payload[campo] = val or None

    for campo in _CAMPOS_DATA:
        payload[campo] = _formata_data(reg.get(campo))

    if not payload["data_abertura"]:
        return None, "data_abertura ausente ou inválida"

    ativo = reg.get("ativo")
    if isinstance(ativo, bool):
        payload["ativo"] = ativo
    elif isinstance(ativo, str):
        payload["ativo"] = ativo.lower() in ("true", "sim", "yes", "1")
    else:
        payload["ativo"] = bool(ativo) if ativo is not None else True

    return payload, None


# ---------------------------------------------------------------------------
# Detecção de colunas (arquivo-base)
# ---------------------------------------------------------------------------

def _detectar_indices(cabecalho):
    idx = {}
    for i, v in enumerate(cabecalho):
        if v is None:
            continue
        nome = str(v).lower().replace("\n", " ").strip()
        if "status" in nome and i == 0:
            idx["status"] = i
        elif ("projeto" in nome and "protocolo" in nome) or (nome == "protocolo" and i == 1):
            idx["col_b"] = i
            idx["col_b_header"] = v
        elif "atividade" in nome:
            idx["atividade"] = i
        elif "atribu" in nome:
            idx["atribuido_a"] = i
        elif "real" in nome and ("início" in nome or "inicio" in nome or "nicio" in nome):
            idx["data_abertura"] = i
        elif "real" in nome and ("término" in nome or "termino" in nome or "rmino" in nome):
            idx["data_finalizacao"] = i
        elif "anota" in nome:
            idx["anotacoes"] = i
        elif "situa" in nome:
            idx["situacao"] = i
        elif "aprova" in nome:
            idx["orgao"] = i
    return idx


# ---------------------------------------------------------------------------
# Parsers por formato
# ---------------------------------------------------------------------------

def _processar_aba_base(ws, nome_aba):
    """Parse uma aba do arquivo-base (cabeçalho na linha 4, dados a partir da linha 5)."""
    registros, ignorados, erros = [], [], []

    try:
        cab = list(next(ws.iter_rows(min_row=4, max_row=4, values_only=True)))
    except StopIteration:
        erros.append({"linha": f"{nome_aba}:4", "erro": "Aba sem cabeçalho na linha 4"})
        return registros, ignorados, erros

    idx = _detectar_indices(cab)
    col_b_header = idx.get("col_b_header", cab[1] if len(cab) > 1 else "")

    for row_num, row in enumerate(ws.iter_rows(min_row=5, values_only=True), start=5):
        if not any(c for c in row if c is not None):
            continue

        linha = f"{nome_aba}:{row_num}"
        try:
            status_raw = _safe_get(row, idx.get("status", 0))
            if not status_raw:
                ignorados.append({"linha": linha, "motivo": "Status ausente"})
                continue

            status = _normaliza_status(status_raw)
            col_b_val = _safe_get(row, idx.get("col_b", 1))
            projeto, protocolo = _extrai_projeto_protocolo(col_b_val, col_b_header, nome_aba)

            atividade = _limpa_texto(_safe_get(row, idx.get("atividade", 2)))
            orgao = _limpa_texto(_safe_get(row, idx.get("orgao", 3)))
            atribuido_a = _limpa_texto(_safe_get(row, idx.get("atribuido_a", 4)))
            data_abertura = _formata_data(_safe_get(row, idx.get("data_abertura", 8)))
            data_finalizacao = _formata_data(_safe_get(row, idx.get("data_finalizacao", 9)))
            situacao = _limpa_texto(_safe_get(row, idx.get("situacao")))

            if not all([status, projeto, protocolo, atividade]):
                ignorados.append({"linha": linha, "motivo": "Campos obrigatórios ausentes"})
                continue

            if not data_abertura:
                ignorados.append({"linha": linha, "motivo": "data_abertura ausente ou inválida"})
                continue

            registros.append({
                "linha": linha,
                "status": status,
                "projeto": projeto,
                "protocolo": protocolo,
                "atividade": atividade,
                "orgao_site_consultado": orgao or "",
                "atribuido_a": atribuido_a,
                "data_abertura": data_abertura,
                "data_finalizacao": data_finalizacao,
                "situacao": situacao,
                "ativo": _inferir_ativo(status, data_finalizacao),
                "url_consulta": None,
                "observacao_consulta": None,
            })
        except Exception as e:
            erros.append({"linha": linha, "erro": str(e)})

    return registros, ignorados, erros


def _processar_carga_inicial(file_buffer):
    """Parse a aba 'Carga Inicial' (formato de saída com colunas já separadas)."""
    registros, ignorados, erros = [], [], []

    try:
        df = pd.read_excel(file_buffer, sheet_name="Carga Inicial", header=3)
    except Exception as e:
        return None, [], [], f"Erro ao ler aba 'Carga Inicial': {str(e)}"

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    for i, row in df.iterrows():
        linha = f"Carga Inicial:{i + 5}"
        try:
            status = str(row.get("status", "")).strip()
            projeto = str(row.get("projeto", "")).strip()
            protocolo = str(row.get("protocolo", "")).strip()
            atividade = str(row.get("atividade", "")).strip()
            orgao = str(row.get("orgao_site_consultado", "")).strip()

            if not all([status, projeto, protocolo, atividade, orgao]):
                ignorados.append({"linha": linha, "motivo": "Campos obrigatórios ausentes"})
                continue

            data_abertura = _formata_data(row.get("data_abertura"))
            if not data_abertura:
                ignorados.append({"linha": linha, "motivo": "data_abertura ausente ou inválida"})
                continue

            data_finalizacao = _formata_data(row.get("data_finalizacao"))
            ativo_raw = str(row.get("ativo", "Sim")).strip().lower()

            registros.append({
                "linha": linha,
                "status": status,
                "projeto": projeto,
                "protocolo": protocolo,
                "atividade": atividade,
                "orgao_site_consultado": orgao,
                "atribuido_a": str(row.get("atribuido_a", "")).strip() or None,
                "data_abertura": data_abertura,
                "data_finalizacao": data_finalizacao,
                "situacao": str(row.get("situacao", "")).strip() or None,
                "ativo": ativo_raw in ("sim", "yes", "true", "1"),
                "url_consulta": str(row.get("url_consulta", "")).strip() or None,
                "observacao_consulta": str(row.get("observacao_consulta", "")).strip() or None,
            })
        except Exception as e:
            erros.append({"linha": linha, "erro": str(e)})

    return registros, ignorados, erros, None


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def parse_spreadsheet(file_buffer) -> dict:
    """
    Parse o arquivo .xlsx e retorna {rows, ignorados, erros} sem tocar no banco.
    Detecta formato automaticamente:
    - Aba 'Carga Inicial' presente → formato de saída (colunas separadas)
    - Sem essa aba → arquivo-base multi-abas ('Projeto – Protocolo' combinados)
    """
    try:
        wb = openpyxl.load_workbook(file_buffer, data_only=True)
        sheet_names = wb.sheetnames
        wb.close()
    except Exception as e:
        return {"error": f"Erro ao abrir arquivo: {str(e)}"}

    file_buffer.seek(0)

    if "Carga Inicial" in sheet_names:
        registros, ignorados, erros, error = _processar_carga_inicial(file_buffer)
        if error:
            return {"error": error}
    else:
        try:
            wb = openpyxl.load_workbook(file_buffer, data_only=True)
        except Exception as e:
            return {"error": f"Erro ao abrir arquivo: {str(e)}"}

        registros, ignorados, erros = [], [], []
        for nome in wb.sheetnames:
            if nome in SKIP_SHEETS:
                continue
            try:
                r, ig, er = _processar_aba_base(wb[nome], nome)
                registros.extend(r)
                ignorados.extend(ig)
                erros.extend(er)
            except Exception as e:
                erros.append({"linha": f"{nome}:?", "erro": f"Erro ao processar aba: {str(e)}"})
        wb.close()

    return {"rows": registros, "ignorados": ignorados, "erros": erros}


def _inserir_rows(rows: list, sb: Client):
    """
    Revalida, checa duplicidade (projeto + protocolo + órgão) e insere cada linha.
    Nunca lança exceção — erros por linha vão para a lista de erros.
    """
    imported, ignorados, erros = [], [], []

    for reg in rows:
        linha = reg.get("linha", "?")
        try:
            payload, erro_validacao = _revalidar_payload(reg)
            if erro_validacao:
                ignorados.append({"linha": linha, "motivo": erro_validacao})
                continue

            projeto = payload["projeto"]
            protocolo = payload["protocolo"]
            orgao = payload.get("orgao_site_consultado") or ""

            existing = (
                sb.table("protocols")
                .select("id")
                .eq("projeto", projeto)
                .eq("protocolo", protocolo)
                .eq("orgao_site_consultado", orgao)
                .execute()
            )
            if existing.data:
                ignorados.append({"linha": linha, "motivo": "Duplicata ignorada"})
                continue

            sb.table("protocols").insert(payload).execute()
            imported.append({"linha": linha, "protocolo": protocolo, "projeto": projeto})
        except Exception as e:
            erros.append({"linha": linha, "erro": str(e)})

    return imported, ignorados, erros


def import_spreadsheet(file_buffer, sb: Client) -> dict:
    """Parse + insere em uma etapa só (endpoint legado /spreadsheet)."""
    parsed = parse_spreadsheet(file_buffer)
    if "error" in parsed:
        return parsed

    imported, ignorados_new, erros_new = _inserir_rows(parsed["rows"], sb)
    return {
        "importados": imported,
        "ignorados": parsed["ignorados"] + ignorados_new,
        "erros": parsed["erros"] + erros_new,
    }


def confirm_import(rows: list, sb: Client) -> dict:
    """Revalida e insere as linhas enviadas pelo frontend após o preview."""
    imported, ignorados, erros = _inserir_rows(rows, sb)
    return {"importados": imported, "ignorados": ignorados, "erros": erros}
