from datetime import date, datetime
import json
from typing import Optional, List
from pydantic import BaseModel, field_validator, model_validator


def _strip_or_none(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


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
    anotacoes: Optional[str] = None
    ativo: bool = True
    url_consulta: Optional[str] = None

    @field_validator("orgao_site_consultado", "atribuido_a", "anotacoes", mode="before")
    @classmethod
    def strip_text_fields(cls, v):
        return _strip_or_none(v) if v is not None and v != "" else v

    @model_validator(mode="after")
    def validate_regra4(self):
        if not (self.orgao_site_consultado or "").strip():
            raise ValueError("Órgão / site consultado é obrigatório")
        if self.ativo and not (self.atribuido_a or "").strip():
            raise ValueError("Atribuído a é obrigatório para protocolo ativo")
        return self


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
    anotacoes: Optional[str] = None
    ativo: Optional[bool] = None
    url_consulta: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def clean_empty_dates(cls, data):
        if isinstance(data, dict):
            for key in ("data_abertura", "data_finalizacao"):
                if data.get(key) == "":
                    data[key] = None
            for key in ("orgao_site_consultado", "atribuido_a", "anotacoes"):
                if key in data and data[key] is not None:
                    data[key] = _strip_or_none(data[key])
        return data


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
    fonte_consulta: Optional[str] = None
    status_anterior: Optional[str] = None

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
