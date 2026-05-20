from datetime import date, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from sqlalchemy.orm import Session
import io

from app.models.protocol import Protocol


def generate_pdf_report(db: Session) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#1a365d"))
    h2_style = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#2b6cb0"))

    story.append(Paragraph("Relatório de Protocolos por Empreendimento", title_style))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 12))

    protocols = db.query(Protocol).order_by(Protocol.projeto, Protocol.protocolo).all()
    por_projeto: dict = {}
    for p in protocols:
        por_projeto.setdefault(p.projeto, []).append(p)

    for projeto, items in por_projeto.items():
        story.append(Paragraph(f"Empreendimento: {projeto}", h2_style))

        table_data = [["Protocolo", "Atividade", "Status", "Situação", "Duração (dias)", "Última Consulta", "Mudança"]]
        for p in items:
            fim = p.data_finalizacao or date.today()
            duracao = (fim - p.data_abertura).days if p.data_abertura else "-"
            ultima = p.ultima_consulta.strftime("%d/%m/%Y") if p.ultima_consulta else "-"
            mudanca = "Sim" if (p.historico and p.historico[-1].houve_mudanca) else "Não"
            table_data.append([
                p.protocolo, p.atividade[:30], p.status,
                p.situacao or "-", str(duracao), ultima, mudanca,
            ])

        t = Table(table_data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ebf8ff")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(Spacer(1, 16))

    doc.build(story)
    return buffer.getvalue()
