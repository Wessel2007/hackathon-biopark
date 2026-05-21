from datetime import date, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from app.supabase_client import SupabaseClient
import io


def generate_pdf_report(sb: SupabaseClient) -> bytes:
    protocols = sb.table("protocols").select("*, query_history(*)").order("projeto").execute().data

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#1a365d"))
    h2_style = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#2b6cb0"))

    story = []
    story.append(Paragraph("Relatório de Protocolos por Empreendimento", title_style))
    story.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 12))

    por_projeto: dict = {}
    for p in protocols:
        por_projeto.setdefault(p["projeto"], []).append(p)

    for projeto, items in por_projeto.items():
        story.append(Paragraph(f"Empreendimento: {projeto}", h2_style))
        table_data = [["Protocolo", "Atividade", "Status", "Situação", "Duração (dias)", "Última Consulta", "Mudança"]]
        for p in items:
            abertura = p.get("data_abertura")
            fim = p.get("data_finalizacao")
            duracao = "-"
            if abertura:
                d_abertura = date.fromisoformat(abertura)
                d_fim = date.fromisoformat(fim) if fim else date.today()
                duracao = str((d_fim - d_abertura).days)

            ultima = p.get("ultima_consulta")
            ultima_str = datetime.fromisoformat(ultima).strftime("%d/%m/%Y") if ultima else "-"

            historico = p.get("query_history") or []
            mudanca = "Sim" if (historico and historico[-1].get("houve_mudanca")) else "Não"

            table_data.append([
                p["protocolo"],
                (p.get("atividade") or "")[:30],
                p["status"],
                p.get("situacao") or "-",
                duracao,
                ultima_str,
                mudanca,
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
