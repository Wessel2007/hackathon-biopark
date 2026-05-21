from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Protocol(Base):
    __tablename__ = "protocols"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), nullable=False)
    projeto = Column(String(200), nullable=False, index=True)
    protocolo = Column(String(100), nullable=False, index=True)
    atividade = Column(String(200), nullable=False)
    orgao_site_consultado = Column(String(200), nullable=False)
    atribuido_a = Column(String(100))
    data_abertura = Column(Date, nullable=False)
    data_finalizacao = Column(Date, nullable=True)
    situacao = Column(String(100))
    anotacoes = Column(Text)
    ativo = Column(Boolean, default=True, nullable=False)
    url_consulta = Column(String(500))
    ultima_consulta = Column(DateTime, nullable=True)
    observacao_consulta = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    historico = relationship("QueryHistory", back_populates="protocol", cascade="all, delete-orphan")


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=False)
    status_consultado = Column(String(100))
    situacao_consultada = Column(String(100))
    observacao = Column(Text)
    texto_bruto = Column(Text)
    houve_mudanca = Column(Boolean, default=False)
    erro = Column(Text)
    data_consulta = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_movimentacao = Column(String(20))
    mudancas_detectadas = Column(Text)
    fonte_consulta = Column(Text)
    status_anterior = Column(Text)

    protocol = relationship("Protocol", back_populates="historico")
