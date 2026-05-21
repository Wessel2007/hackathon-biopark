from datetime import date, datetime
import json
from typing import Optional, List
from pydantic import BaseModel, field_validator


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
    data_movimentacao: Optional[str] = None
    mudancas_detectadas: Optional[List[str]] = None

    @field_validator("mudancas_detectadas", mode="before")
    @classmethod
    def parse_mudancas(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, ValueError):
                return None
        return v

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
