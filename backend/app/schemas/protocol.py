from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class ProtocolBase(BaseModel):
    status: str
    projeto: str
    protocolo: str
    atividade: str
    orgao_site_consultado: str
    atribuido_a: Optional[str] = None
    data_abertura: date
    data_finalizacao: Optional[date] = None
    situacao: Optional[str] = None
    ativo: bool = True
    url_consulta: Optional[str] = None


class ProtocolCreate(ProtocolBase):
    pass


class ProtocolUpdate(BaseModel):
    status: Optional[str] = None
    projeto: Optional[str] = None
    protocolo: Optional[str] = None
    atividade: Optional[str] = None
    orgao_site_consultado: Optional[str] = None
    atribuido_a: Optional[str] = None
    data_abertura: Optional[date] = None
    data_finalizacao: Optional[date] = None
    situacao: Optional[str] = None
    ativo: Optional[bool] = None
    url_consulta: Optional[str] = None


class QueryHistoryOut(BaseModel):
    id: int
    status_consultado: Optional[str]
    situacao_consultada: Optional[str]
    observacao: Optional[str]
    houve_mudanca: bool
    erro: Optional[str]
    data_consulta: datetime

    class Config:
        from_attributes = True


class ProtocolOut(ProtocolBase):
    id: int
    ultima_consulta: Optional[datetime]
    observacao_consulta: Optional[str]
    criado_em: datetime
    atualizado_em: datetime
    duracao_dias: Optional[int] = None
    historico: List[QueryHistoryOut] = []

    class Config:
        from_attributes = True
