import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _html(protocolo: dict, mudancas: list[str]) -> str:
    itens = "".join(f"<li style='margin:6px 0'>{m}</li>" for m in mudancas)
    responsavel = protocolo.get("atribuido_a") or "—"
    status_novo = protocolo.get("status") or "—"
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
      <div style="background:#0d0d0d;padding:20px 28px;border-radius:12px 12px 0 0">
        <h2 style="color:#d4ff3a;margin:0;font-size:18px">Biopark · Atualização de Protocolo</h2>
      </div>
      <div style="background:#f9f9f7;padding:24px 28px;border:1px solid #e5e5e0;border-top:none;border-radius:0 0 12px 12px">
        <p style="margin:0 0 16px;color:#444">
          O protocolo <strong>{protocolo.get("protocolo")}</strong> do projeto
          <strong>{protocolo.get("projeto")}</strong> teve mudanças detectadas:
        </p>
        <ul style="background:#fff;border:1px solid #e5e5e0;border-radius:8px;padding:14px 14px 14px 30px;color:#333">
          {itens}
        </ul>
        <table style="margin-top:16px;width:100%;font-size:13px;color:#666;border-collapse:collapse">
          <tr>
            <td style="padding:4px 0"><strong>Status atual:</strong></td>
            <td>{status_novo}</td>
          </tr>
          <tr>
            <td style="padding:4px 0"><strong>Responsável:</strong></td>
            <td>{responsavel}</td>
          </tr>
          <tr>
            <td style="padding:4px 0"><strong>Órgão:</strong></td>
            <td>{protocolo.get("orgao_site_consultado") or "—"}</td>
          </tr>
        </table>
        <p style="margin-top:20px;font-size:12px;color:#aaa">
          Este é um e-mail automático da plataforma Biopark · Protocolos.
        </p>
      </div>
    </div>
    """


def enviar_alerta(protocolo: dict, mudancas: list[str], user_email: str = "") -> None:
    if not mudancas:
        return

    if not all([settings.smtp_host, settings.smtp_user, settings.smtp_pass]):
        logger.warning("SMTP não configurado — alerta de e-mail ignorado.")
        return

    destinatario = user_email or settings.dashboard_email
    if not destinatario:
        logger.warning("Nenhum destinatário definido — e-mail não enviado.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Biopark] Atualização: protocolo {protocolo.get('protocolo')} — {protocolo.get('projeto')}"
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = destinatario

    msg.attach(MIMEText(_html(protocolo, mudancas), "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(msg["From"], [destinatario], msg.as_string())
        logger.info("Alerta enviado para %s — protocolo %s", destinatario, protocolo.get("protocolo"))
    except Exception as exc:
        logger.error("Falha ao enviar e-mail para %s: %s", destinatario, exc)
