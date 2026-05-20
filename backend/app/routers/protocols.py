from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.protocol import Protocol
from app.schemas.protocol import ProtocolCreate, ProtocolUpdate, ProtocolOut
from app.routers.deps import get_current_user

router = APIRouter(prefix="/protocols", tags=["protocols"])


def _add_duracao(p: Protocol) -> dict:
    data = ProtocolOut.from_orm(p).dict()
    fim = p.data_finalizacao or date.today()
    data["duracao_dias"] = (fim - p.data_abertura).days if p.data_abertura else None
    return data


@router.get("/", response_model=List[ProtocolOut])
def list_protocols(
    projeto: Optional[str] = Query(None),
    ativo: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    q = db.query(Protocol)
    if projeto:
        q = q.filter(Protocol.projeto.ilike(f"%{projeto}%"))
    if ativo is not None:
        q = q.filter(Protocol.ativo == ativo)
    if status:
        q = q.filter(Protocol.status == status)
    return [_add_duracao(p) for p in q.offset(skip).limit(limit).all()]


@router.get("/{protocol_id}", response_model=ProtocolOut)
def get_protocol(protocol_id: int, db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    p = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    return _add_duracao(p)


@router.post("/", response_model=ProtocolOut, status_code=201)
def create_protocol(body: ProtocolCreate, db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    existing = db.query(Protocol).filter(
        Protocol.projeto == body.projeto, Protocol.protocolo == body.protocolo
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Protocolo já cadastrado para este projeto")
    p = Protocol(**body.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return _add_duracao(p)


@router.patch("/{protocol_id}", response_model=ProtocolOut)
def update_protocol(
    protocol_id: int, body: ProtocolUpdate, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    p = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    for field, value in body.dict(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return _add_duracao(p)


@router.delete("/{protocol_id}", status_code=204)
def delete_or_inactivate_protocol(
    protocol_id: int, force: bool = False, db: Session = Depends(get_db), _: str = Depends(get_current_user)
):
    p = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Protocolo não encontrado")
    if p.historico and not force:
        p.ativo = False
        db.commit()
    else:
        db.delete(p)
        db.commit()
