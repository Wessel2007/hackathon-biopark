from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.supabase_client import SupabaseClient, get_supabase
from app.schemas.protocol import ProtocolCreate, ProtocolUpdate
from app.routers.deps import get_current_user

router = APIRouter(prefix="/protocols", tags=["protocols"])


def _add_duracao(p: dict) -> dict:
    abertura = p.get("data_abertura")
    fim = p.get("data_finalizacao")
    if abertura:
        d_abertura = date.fromisoformat(abertura)
        d_fim = date.fromisoformat(fim) if fim else date.today()
        p["duracao_dias"] = (d_fim - d_abertura).days
    else:
        p["duracao_dias"] = None
    return p


@router.get("/")
def list_protocols(
    projeto: Optional[str] = Query(None),
    ativo: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    sb: SupabaseClient = Depends(get_supabase),
    _: str = Depends(get_current_user),
):
    q = sb.table("protocols").select("*, query_history(*)")
    if projeto:
        q = q.ilike("projeto", f"%{projeto}%")
    if ativo is not None:
        q = q.eq("ativo", ativo)
    if status:
        q = q.eq("status", status)
    result = q.range(skip, skip + limit - 1).order("projeto").execute()
    return [_add_duracao(p) for p in result.data]


@router.get("/{protocol_id}")
def get_protocol(protocol_id: int, sb: SupabaseClient = Depends(get_supabase), _: str = Depends(get_current_user)):
    result = sb.table("protocols").select("*, query_history(*)").eq("id", protocol_id).maybe_single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    return _add_duracao(result.data)


@router.post("/", status_code=201)
def create_protocol(body: ProtocolCreate, sb: SupabaseClient = Depends(get_supabase), _: str = Depends(get_current_user)):
    existing = sb.table("protocols").select("id").eq("projeto", body.projeto).eq("protocolo", body.protocolo).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="Protocolo já cadastrado para este projeto")
    payload = body.model_dump()
    for k, v in payload.items():
        if hasattr(v, "isoformat"):
            payload[k] = v.isoformat()
    result = sb.table("protocols").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar protocolo no banco de dados")
    return _add_duracao(result.data[0])


@router.patch("/{protocol_id}")
def update_protocol(
    protocol_id: int, body: ProtocolUpdate, sb: SupabaseClient = Depends(get_supabase), _: str = Depends(get_current_user)
):
    existing = sb.table("protocols").select("id").eq("id", protocol_id).maybe_single().execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    payload = {k: v for k, v in body.model_dump(exclude_unset=True).items()}
    for k, v in payload.items():
        if hasattr(v, "isoformat"):
            payload[k] = v.isoformat()
    result = sb.table("protocols").update(payload).eq("id", protocol_id).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao atualizar protocolo no banco de dados")
    return _add_duracao(result.data[0])


@router.delete("/{protocol_id}", status_code=204)
def delete_protocol(
    protocol_id: int, force: bool = False, sb: SupabaseClient = Depends(get_supabase), _: str = Depends(get_current_user)
):
    existing = sb.table("protocols").select("id").eq("id", protocol_id).maybe_single().execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    history = sb.table("query_history").select("id").eq("protocol_id", protocol_id).limit(1).execute()
    if history.data and not force:
        sb.table("protocols").update({"ativo": False}).eq("id", protocol_id).execute()
    else:
        sb.table("protocols").delete().eq("id", protocol_id).execute()
