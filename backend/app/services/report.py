from datetime import date, datetime
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.supabase_client import SupabaseClient
from app.services.protocol_metrics import (
    calc_duracao,
    classificar_protocolo,
    format_datetime_consulta,
    observacao_atual,
    ultima_consulta,
)


def _style_table(header_color="#2b6cb0"):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ebf8ff")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])


def _build_table(headers: list, rows: list, col_widths=None) -> Table:
    data = [headers] + (rows or [["—"] * len(headers)])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(_style_table())
    return t


def _section_title(story, text: str, h2_style):
    story.append(Spacer(1, 8))
    story.append(Paragraph(text, h2_style))
    story.append(Spacer(1, 6))


def generate_pdf_report(sb: SupabaseClient) -> bytes:
    protocols = sb.table("protocols").select("*, query_history(*)").order("projeto").execute().data
    today = date.today()
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    classificados = {c: [] for c in ("mudanca", "erro", "sem_atualizacao", "ok")}
    for p in protocols:
        classificados[classificar_protocolo(p, today)].append(p)

    total = len(protocols)
    ativos = sum(1 for p in protocols if p.get("ativo"))
    duracoes = [d for p in protocols if (d := calc_duracao(p)) is not None]
    duracao_media = round(sum(duracoes) / len(duracoes), 1) if duracoes else 0

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#1a365d")
    )
    h2_style = ParagraphStyle(
        "h2", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#2b6cb0")
    )
    normal = styles["Normal"]

    story = []
    story.append(Paragraph("Relatório de Protocolos por Empreendimento", title_style))
    story.append(Paragraph(f"Gerado em: {now_str}", normal))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 12))

    # Resumo geral
    _section_title(story, "Resumo geral", h2_style)
    resumo = [
        ["Indicador", "Valor"],
        ["Total de protocolos", str(total)],
        ["Protocolos ativos", str(ativos)],
        ["Com mudança na última consulta", str(len(classificados["mudanca"]))],
        ["Com erro na última consulta", str(len(classificados["erro"]))],
        ["Sem atualização (nunca consultados ou &gt; 30 dias)", str(len(classificados["sem_atualizacao"]))],
        ["Duração média (dias)", str(duracao_media)],
    ]
    story.append(_build_table(resumo[0], resumo[1:]))
    story.append(Spacer(1, 16))

    # Protocolos com mudança
    _section_title(story, "Protocolos com mudança de status", h2_style)
    mud_rows = []
    for p in classificados["mudanca"]:
        last = ultima_consulta(p.get("query_history") or [])
        status_ant = (last.get("status_anterior") if last else None) or "—"
        status_at = (last.get("status_consultado") if last else None) or p.get("status", "—")
        mud_rows.append([
            p.get("projeto", "—")[:25],
            p.get("protocolo", "—"),
            (p.get("orgao_site_consultado") or "—")[:22],
            f"{status_ant} → {status_at}",
            observacao_atual(p)[:40],
            format_datetime_consulta(p.get("ultima_consulta")),
        ])
    story.append(_build_table(
        ["Projeto", "Protocolo", "Órgão", "Status", "Observação", "Última consulta"],
        mud_rows,
    ))
    story.append(Spacer(1, 16))

    # Protocolos com erro
    _section_title(story, "Protocolos com erro de consulta", h2_style)
    err_rows = []
    for p in classificados["erro"]:
        last = ultima_consulta(p.get("query_history") or [])
        err_rows.append([
            p.get("projeto", "—")[:25],
            p.get("protocolo", "—"),
            (p.get("orgao_site_consultado") or "—")[:22],
            (last.get("erro") if last else "—")[:50],
            format_datetime_consulta(last.get("data_consulta") if last else None),
        ])
    story.append(_build_table(
        ["Projeto", "Protocolo", "Órgão", "Erro", "Data consulta"],
        err_rows,
    ))
    story.append(Spacer(1, 16))

    # Sem atualização
    _section_title(story, "Protocolos sem atualização", h2_style)
    sem_rows = []
    for p in classificados["sem_atualizacao"]:
        hist = p.get("query_history") or []
        motivo = "Nunca consultado" if not hist else "Última consulta há mais de 30 dias"
        sem_rows.append([
            p.get("projeto", "—")[:25],
            p.get("protocolo", "—"),
            (p.get("orgao_site_consultado") or "—")[:22],
            p.get("status", "—"),
            motivo,
            format_datetime_consulta(p.get("ultima_consulta")),
        ])
    story.append(_build_table(
        ["Projeto", "Protocolo", "Órgão", "Status", "Motivo", "Última consulta"],
        sem_rows,
    ))
    story.append(Spacer(1, 16))

    # Por empreendimento
    _section_title(story, "Protocolos por empreendimento", h2_style)
    por_projeto: dict = {}
    for p in protocols:
        por_projeto.setdefault(p["projeto"], []).append(p)

    for projeto, items in por_projeto.items():
        story.append(Paragraph(f"Empreendimento: {projeto}", h2_style))
        table_data = []
        for p in items:
            dur = calc_duracao(p)
            last = ultima_consulta(p.get("query_history") or [])
            mudanca = "Sim" if (last and last.get("houve_mudanca")) else "Não"
            table_data.append([
                p.get("protocolo", "—"),
                (p.get("atividade") or "")[:28],
                (p.get("orgao_site_consultado") or "—")[:18],
                p.get("status", "—"),
                p.get("situacao") or "—",
                str(dur) if dur is not None else "—",
                format_datetime_consulta(p.get("ultima_consulta")),
                observacao_atual(p)[:35],
                mudanca,
            ])
        story.append(_build_table(
            [
                "Protocolo", "Atividade", "Órgão", "Status", "Situação",
                "Duração", "Última consulta", "Observação", "Mudança",
            ],
            table_data,
        ))
        story.append(Spacer(1, 16))

    doc.build(story)
    return buffer.getvalue()
