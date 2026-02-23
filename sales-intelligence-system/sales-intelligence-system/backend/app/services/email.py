"""Email service via Resend API."""

import logging
import resend
from app.core.config import get_settings

log = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str, html: bool = False) -> dict:
    """Send an email via Resend.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text or HTML)
        html: If True, body is treated as HTML

    Returns:
        Send result dict
    """
    settings = get_settings()

    if not settings.resend_api_key:
        log.warning("Resend API key not configured. Skipping email.")
        return {"status": "skipped", "reason": "no_api_key"}

    resend.api_key = settings.resend_api_key

    try:
        params = {
            "from": settings.from_email,
            "to": [to],
            "subject": subject,
        }

        if html:
            params["html"] = body
        else:
            params["text"] = body

        result = resend.Emails.send(params)
        log.info(f"Email sent to {to}: {subject}")
        return {"status": "sent", "id": result.get("id")}

    except Exception as e:
        log.error(f"Email failed to {to}: {e}")
        return {"status": "error", "error": str(e)}


async def send_morning_brief_email(to: str, rep_name: str, brief_content: str, date_str: str) -> dict:
    """Send formatted morning brief email."""
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #1e293b; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">Good Morning, {rep_name}</h1>
            <p style="margin: 5px 0 0; opacity: 0.8; font-size: 14px;">{date_str} | Sales Intelligence Brief</p>
        </div>
        <div style="background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px;">
            <pre style="font-family: inherit; white-space: pre-wrap; line-height: 1.6; font-size: 14px; color: #334155;">{brief_content}</pre>
        </div>
        <p style="text-align: center; font-size: 12px; color: #94a3b8; margin-top: 16px;">
            Powered by Sales Intelligence Agent | Onsite Teams
        </p>
    </div>
    """
    return await send_email(to, f"Morning Brief — {date_str}", html, html=True)


async def send_weekly_report_email(to: str, report_content: str, week_str: str) -> dict:
    """Send formatted weekly report email."""
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
        <div style="background: #0f172a; color: white; padding: 24px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 22px;">Weekly Intelligence Report</h1>
            <p style="margin: 5px 0 0; opacity: 0.8; font-size: 14px;">Week of {week_str}</p>
        </div>
        <div style="background: white; padding: 24px; border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px;">
            <pre style="font-family: inherit; white-space: pre-wrap; line-height: 1.7; font-size: 14px; color: #1e293b;">{report_content}</pre>
        </div>
        <p style="text-align: center; font-size: 12px; color: #94a3b8; margin-top: 16px;">
            Sales Intelligence Agent | Onsite Teams
        </p>
    </div>
    """
    return await send_email(to, f"Weekly Sales Report — {week_str}", html, html=True)
