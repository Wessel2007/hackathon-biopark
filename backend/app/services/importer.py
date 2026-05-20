import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.protocol import Protocol


REQUIRED_COLUMNS = {"status", "projeto", "protocolo", "atividade", "orgao_site_consultado", "data_abertura"}


def import_spreadsheet(file_buffer, db: Session) -> dict:
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

            if pd.isna(data_abertura_raw):
                skipped.append({"linha": linha, "motivo": "data_abertura ausente"})
                continue

            data_abertura = pd.to_datetime(data_abertura_raw).date()

            data_finalizacao_raw = row.get("data_finalizacao")
            data_finalizacao = None
            if not pd.isna(data_finalizacao_raw) if data_finalizacao_raw is not None else False:
                data_finalizacao = pd.to_datetime(data_finalizacao_raw).date()

            existing = db.query(Protocol).filter(
                Protocol.projeto == projeto, Protocol.protocolo == protocolo
            ).first()
            if existing:
                skipped.append({"linha": linha, "motivo": "Duplicata ignorada"})
                continue

            ativo_raw = str(row.get("ativo", "Sim")).strip().lower()
            ativo = ativo_raw in ("sim", "yes", "true", "1")

            p = Protocol(
                status=status,
                projeto=projeto,
                protocolo=protocolo,
                atividade=atividade,
                orgao_site_consultado=orgao,
                atribuido_a=str(row.get("atribuido_a", "")).strip() or None,
                data_abertura=data_abertura,
                data_finalizacao=data_finalizacao,
                situacao=str(row.get("situacao", "")).strip() or None,
                anotacoes=str(row.get("anotacoes", "")).strip() or None,
                ativo=ativo,
                url_consulta=str(row.get("url_consulta", "")).strip() or None,
                observacao_consulta=str(row.get("observacao_consulta", "")).strip() or None,
            )
            db.add(p)
            imported.append({"linha": linha, "protocolo": protocolo, "projeto": projeto})

        except Exception as e:
            errors.append({"linha": linha, "erro": str(e)})

    db.commit()
    return {"importados": imported, "ignorados": skipped, "erros": errors}
