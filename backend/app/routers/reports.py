from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.database import get_db
from app.services.report import generate_pdf_report
from app.routers.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/pdf")
def get_pdf_report(db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    pdf_bytes = generate_pdf_report(db)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=relatorio_protocolos.pdf"},
    )


@router.get("/dashboard-data")
def get_dashboard_data(db: Session = Depends(get_db), _: str = Depends(get_current_user)):
    from app.models.protocol import Protocol, QueryHistory
    from datetime import date
    from sqlalchemy import func

    protocols = db.query(Protocol).all()
    total = len(protocols)
    ativos = sum(1 for p in protocols if p.ativo)
    com_mudanca = sum(
        1 for p in protocols
        if p.historico and p.historico[-1].houve_mudanca
    )
    por_projeto = {}
    for p in protocols:
        por_projeto.setdefault(p.projeto, []).append({
            "id": p.id,
            "protocolo": p.protocolo,
            "status": p.status,
            "situacao": p.situacao,
            "ativo": p.ativo,
            "ultima_consulta": p.ultima_consulta.isoformat() if p.ultima_consulta else None,
            "houve_mudanca": bool(p.historico and p.historico[-1].houve_mudanca),
            "duracao_dias": ((p.data_finalizacao or date.today()) - p.data_abertura).days if p.data_abertura else None,
        })

    return {
        "total": total,
        "ativos": ativos,
        "com_mudanca_recente": com_mudanca,
        "por_projeto": por_projeto,
    }
