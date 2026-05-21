import pandas as pd
from supabase import Client


def import_spreadsheet(file_buffer, sb: Client) -> dict:
    try:
        df = pd.read_excel(file_buffer, sheet_name="Carga Inicial", header=3)
    except Exception as e:
        return {"error": f"Erro ao ler planilha: {str(e)}"}

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    imported, skipped, errors = [], [], []

    for idx, row in df.iterrows():
        linha = idx + 5
        try:
            status = str(row.get("status", "")).strip()
            projeto = str(row.get("projeto", "")).strip()
            protocolo = str(row.get("protocolo", "")).strip()
            atividade = str(row.get("atividade", "")).strip()
            orgao = str(row.get("orgao_site_consultado", "")).strip()
            data_abertura_raw = row.get("data_abertura")

            if not all([status, projeto, protocolo, atividade, orgao]):
                skipped.append({"linha": linha, "motivo": "Campos obrigatórios ausentes"})
                continue

            if pd.isna(data_abertura_raw) if data_abertura_raw is None else False:
                skipped.append({"linha": linha, "motivo": "data_abertura ausente"})
                continue

            try:
                data_abertura = pd.to_datetime(data_abertura_raw).date().isoformat()
            except Exception:
                skipped.append({"linha": linha, "motivo": "data_abertura inválida"})
                continue

            data_finalizacao_raw = row.get("data_finalizacao")
            data_finalizacao = None
            try:
                if data_finalizacao_raw and not pd.isna(data_finalizacao_raw):
                    data_finalizacao = pd.to_datetime(data_finalizacao_raw).date().isoformat()
            except Exception:
                pass

            existing = sb.table("protocols").select("id").eq("projeto", projeto).eq("protocolo", protocolo).execute()
            if existing.data:
                skipped.append({"linha": linha, "motivo": "Duplicata ignorada"})
                continue

            ativo_raw = str(row.get("ativo", "Sim")).strip().lower()
            ativo = ativo_raw in ("sim", "yes", "true", "1")

            payload = {
                "status": status,
                "projeto": projeto,
                "protocolo": protocolo,
                "atividade": atividade,
                "orgao_site_consultado": orgao,
                "atribuido_a": str(row.get("atribuido_a", "")).strip() or None,
                "data_abertura": data_abertura,
                "data_finalizacao": data_finalizacao,
                "situacao": str(row.get("situacao", "")).strip() or None,
                "anotacoes": str(row.get("anotacoes", "")).strip() or None,
                "ativo": ativo,
                "url_consulta": str(row.get("url_consulta", "")).strip() or None,
                "observacao_consulta": str(row.get("observacao_consulta", "")).strip() or None,
            }
            sb.table("protocols").insert(payload).execute()
            imported.append({"linha": linha, "protocolo": protocolo, "projeto": projeto})

        except Exception as e:
            errors.append({"linha": linha, "erro": str(e)})

    return {"importados": imported, "ignorados": skipped, "erros": errors}
