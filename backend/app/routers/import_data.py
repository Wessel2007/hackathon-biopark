from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from supabase import Client
import io

from app.supabase_client import get_supabase
from app.services.importer import import_spreadsheet
from app.routers.deps import get_current_user

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/spreadsheet")
def import_excel(
    file: UploadFile = File(...),
    sb: Client = Depends(get_supabase),
    _: str = Depends(get_current_user),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .xlsx ou .xls")
    contents = file.file.read()
    result = import_spreadsheet(io.BytesIO(contents), sb)
    return result
