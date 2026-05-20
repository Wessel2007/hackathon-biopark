from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.protocol import Protocol, QueryHistory


def _scrape_url(url: str) -> dict:
    """Tenta acessar o site e extrair informações. Retorna dict com status/observacao/erro."""
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Heurística básica — adaptar conforme o site real
        texto = soup.get_text(separator=" ", strip=True)
        return {
            "status_consultado": _extract_status(texto),
            "observacao": texto[:500],
            "texto_bruto": texto[:2000],
            "erro": None,
        }
    except Exception as e:
        return {
            "status_consultado": None,
            "observacao": None,
            "texto_bruto": None,
            "erro": str(e),
        }


def _extract_status(texto: str) -> str:
    """Heurística simples de extração de status — adaptar por órgão."""
    texto_lower = texto.lower()
    if "aprovado" in texto_lower or "deferido" in texto_lower:
        return "APRO"
    if "indeferido" in texto_lower or "reprovado" in texto_lower:
        return "REPROVADO"
    if "análise" in texto_lower or "andamento" in texto_lower:
        return "EM ANDAMENTO"
    if "aguardando" in texto_lower:
        return "AGUARDANDO DOCUMENTACAO"
    if "cancelado" in texto_lower:
        return "CANCELADO"
    return "PENDENTE"


def _simulate_query(p: Protocol) -> dict:
    """Simula uma consulta quando não há URL ou o site está inacessível."""
    return {
        "status_consultado": p.status,
        "observacao": f"[SIMULADO] Protocolo {p.protocolo} - {p.situacao}",
        "texto_bruto": None,
        "erro": None,
    }


def run_single_query(protocol_id: int, db: Session) -> dict:
    p = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not p:
        return {"erro": "Protocolo não encontrado"}

    if p.url_consulta:
        resultado = _scrape_url(p.url_consulta)
    else:
        resultado = _simulate_query(p)

    ultimo = p.historico[-1] if p.historico else None
    houve_mudanca = bool(
        ultimo and ultimo.status_consultado != resultado["status_consultado"]
    )

    history = QueryHistory(
        protocol_id=p.id,
        status_consultado=resultado["status_consultado"],
        observacao=resultado["observacao"],
        texto_bruto=resultado["texto_bruto"],
        houve_mudanca=houve_mudanca,
        erro=resultado["erro"],
        data_consulta=datetime.utcnow(),
    )
    db.add(history)

    p.ultima_consulta = datetime.utcnow()
    p.observacao_consulta = resultado["observacao"]
    if resultado["status_consultado"] and not resultado["erro"]:
        p.status = resultado["status_consultado"]

    db.commit()
    return {"protocolo": p.protocolo, "resultado": resultado, "houve_mudanca": houve_mudanca}


def run_all_queries(db: Session):
    protocols = db.query(Protocol).filter(Protocol.ativo == True).all()
    for p in protocols:
        run_single_query(p.id, db)
