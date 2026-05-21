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

# A4 usable width: 595 - 40 (left) - 40 (right) = 515pt
_PAGE_W = 515


def _style_table(header_color="#2b6cb0"):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ebf8ff")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])


def _cell_style():
    styles = getSampleStyleSheet()
    return ParagraphStyle(
        "cell", parent=styles["Normal"], fontSize=7, leading=9, wordWrap="CJK",
    )


def _wrap(text, style) -> Paragraph:
    return Paragraph(str(text) if text else "—", style)


def _build_table(headers: list, rows: list, col_widths: list) -> Table:
    cell_st = _cell_style()
    wrapped_rows = []
    for row in (rows or [["—"] * len(headers)]):
        wrapped_rows.append([_wrap(cell, cell_st) for cell in row])
    data = [headers] + wrapped_rows
    t = Table(data, colWidths=col_widths, repeatRows=1, splitByRow=1)
    t.setStyle(_style_table())
    return t


def _section_title(story, text: str, h2_style):
    story.append(Spacer(1, 8))
    story.append(Paragraph(text, h2_style))
    story.append(Spacer(1, 6))


def generate_pdf_report(sb: SupabaseClient, filters: dict | None = None) -> bytes:
    filters = filters or {}
    today = date.today()
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    q = sb.table("protocols").select("*, query_history(*)").order("projeto")
    if filters.get("projeto"):
        q = q.ilike("projeto", f"%{filters['projeto']}%")
    if filters.get("orgao"):
        q = q.ilike("orgao_site_consultado", f"%{filters['orgao']}%")
    if filters.get("status"):
        q = q.eq("status", filters["status"])
    if filters.get("ativo") is not None:
        q = q.eq("ativo", filters["ativo"])
    if filters.get("atribuido_a"):
        q = q.ilike("atribuido_a", f"%{filters['atribuido_a']}%")
    if filters.get("situacao"):
        q = q.ilike("situacao", f"%{filters['situacao']}%")
    if filters.get("data_abertura_inicio"):
        q = q.gte("data_abertura", str(filters["data_abertura_inicio"]))
    if filters.get("data_abertura_fim"):
        q = q.lte("data_abertura", str(filters["data_abertura_fim"]))

    protocols = q.execute().data

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
    filter_style = ParagraphStyle(
        "filter_note", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#555555"),
        backColor=colors.HexColor("#f0f4ff"), borderPadding=4,
    )
    normal = styles["Normal"]

    story = []
    story.append(Paragraph("Relatório de Protocolos por Empreendimento", title_style))
    story.append(Paragraph(f"Gerado em: {now_str}", normal))

    # Filtros ativos
    active_filters = []
    if filters.get("projeto"):
        active_filters.append(f"Projeto: {filters['projeto']}")
    if filters.get("orgao"):
        active_filters.append(f"Órgão: {filters['orgao']}")
    if filters.get("status"):
        active_filters.append(f"Status: {filters['status']}")
    if filters.get("ativo") is not None:
        active_filters.append("Apenas ativos" if filters["ativo"] else "Apenas inativos")
    if filters.get("atribuido_a"):
        active_filters.append(f"Atribuído a: {filters['atribuido_a']}")
    if filters.get("situacao"):
        active_filters.append(f"Situação: {filters['situacao']}")
    if filters.get("data_abertura_inicio"):
        active_filters.append(f"Abertura a partir de: {filters['data_abertura_inicio']}")
    if filters.get("data_abertura_fim"):
        active_filters.append(f"Abertura até: {filters['data_abertura_fim']}")

    if active_filters:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Filtros aplicados: {' · '.join(active_filters)}", filter_style))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 12))

    # Resumo geral — 2 colunas [300, 215] = 515
    _section_title(story, "Resumo geral", h2_style)
    resumo = [
        ["Indicador", "Valor"],
        ["Total de protocolos", str(total)],
        ["Protocolos ativos", str(ativos)],
        ["Com mudança na última consulta", str(len(classificados["mudanca"]))],
        ["Com erro na última consulta", str(len(classificados["erro"]))],
        ["Sem atualização (nunca consultados ou > 30 dias)", str(len(classificados["sem_atualizacao"]))],
        ["Duração média (dias)", str(duracao_media)],
    ]
    story.append(_build_table(resumo[0], resumo[1:], col_widths=[300, 215]))
    story.append(Spacer(1, 16))

    # Protocolos com mudança — 6 colunas [95, 80, 80, 110, 95, 55] = 515
    _section_title(story, "Protocolos com mudança de status", h2_style)
    mud_rows = []
    for p in classificados["mudanca"]:
        last = ultima_consulta(p.get("query_history") or [])
        status_ant = (last.get("status_anterior") if last else None) or "—"
        status_at = (last.get("status_consultado") if last else None) or p.get("status", "—")
        mud_rows.append([
            p.get("projeto", "—"),
            p.get("protocolo", "—"),
            p.get("orgao_site_consultado") or "—",
            f"{status_ant} → {status_at}",
            observacao_atual(p),
            format_datetime_consulta(p.get("ultima_consulta")),
        ])
    story.append(_build_table(
        ["Projeto", "Protocolo", "Órgão", "Status", "Observação", "Última consulta"],
        mud_rows,
        col_widths=[95, 80, 80, 110, 95, 55],
    ))
    story.append(Spacer(1, 16))

    # Protocolos com erro — 5 colunas [90, 80, 80, 210, 55] = 515
    _section_title(story, "Protocolos com erro de consulta", h2_style)
    err_rows = []
    for p in classificados["erro"]:
        last = ultima_consulta(p.get("query_history") or [])
        err_rows.append([
            p.get("projeto", "—"),
            p.get("protocolo", "—"),
            p.get("orgao_site_consultado") or "—",
            (last.get("erro") if last else "—"),
            format_datetime_consulta(last.get("data_consulta") if last else None),
        ])
    story.append(_build_table(
        ["Projeto", "Protocolo", "Órgão", "Erro", "Data consulta"],
        err_rows,
        col_widths=[90, 80, 80, 210, 55],
    ))
    story.append(Spacer(1, 16))

    # Sem atualização — 6 colunas [90, 80, 80, 70, 140, 55] = 515
    _section_title(story, "Protocolos sem atualização", h2_style)
    sem_rows = []
    for p in classificados["sem_atualizacao"]:
        hist = p.get("query_history") or []
        motivo = "Nunca consultado" if not hist else "Última consulta há mais de 30 dias"
        sem_rows.append([
            p.get("projeto", "—"),
            p.get("protocolo", "—"),
            p.get("orgao_site_consultado") or "—",
            p.get("status", "—"),
            motivo,
            format_datetime_consulta(p.get("ultima_consulta")),
        ])
    story.append(_build_table(
        ["Projeto", "Protocolo", "Órgão", "Status", "Motivo", "Última consulta"],
        sem_rows,
        col_widths=[90, 80, 80, 70, 140, 55],
    ))
    story.append(Spacer(1, 16))

    # Por empreendimento — 9 colunas [65, 65, 60, 58, 55, 60, 35, 57, 60] = 515
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
                p.get("orgao_site_consultado") or "—",
                p.get("status", "—"),
                p.get("situacao") or "—",
                p.get("atribuido_a") or "—",
                str(dur) if dur is not None else "—",
                format_datetime_consulta(p.get("ultima_consulta")),
                observacao_atual(p),
                mudanca,
            ])
        story.append(_build_table(
            ["Protocolo", "Órgão", "Status", "Situação", "Atribuído a", "Dur.", "Última consulta", "Observação", "Mud."],
            table_data,
            col_widths=[65, 65, 60, 58, 65, 32, 57, 88, 25],
        ))
        story.append(Spacer(1, 16))

    doc.build(story)
    return buffer.getvalue()
