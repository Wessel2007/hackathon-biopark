from typing import List

import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.routers.deps import get_current_user
from app.services.importer import confirm_import, import_spreadsheet, parse_spreadsheet
from app.supabase_client import SupabaseClient, get_supabase

router = APIRouter(prefix="/import", tags=["import"])


def _validate_xlsx(file: UploadFile):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .xlsx ou .xls")


@router.post("/preview")
def preview_excel(
    file: UploadFile = File(...),
    _: str = Depends(get_current_user),
):
    """Parse o arquivo e retorna linhas + erros sem salvar no banco."""
    _validate_xlsx(file)
    result = parse_spreadsheet(io.BytesIO(file.file.read()))
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


class ConfirmBody(BaseModel):
    rows: List[dict]


@router.post("/confirm")
def confirm_excel(
    body: ConfirmBody,
    sb: SupabaseClient = Depends(get_supabase),
    _: str = Depends(get_current_user),
):
    """Recebe as linhas validadas do preview e as insere no banco."""
    return confirm_import(body.rows, sb)


@router.post("/spreadsheet")
def import_excel(
    file: UploadFile = File(...),
    sb: SupabaseClient = Depends(get_supabase),
    _: str = Depends(get_current_user),
):
    """Importação direta sem preview (mantido para compatibilidade)."""
    _validate_xlsx(file)
    result = import_spreadsheet(io.BytesIO(file.file.read()), sb)
    return result
