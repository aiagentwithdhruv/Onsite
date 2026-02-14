"""WhatsApp messaging via Gupshup API."""

import logging
import httpx
from app.core.config import get_settings

log = logging.getLogger(__name__)


async def send_whatsapp_message(phone: str, message: str) -> dict:
    """Send a WhatsApp text message via Gupshup.

    Args:
        phone: Recipient phone number with country code (e.g., "919876543210")
        message: Text message to send (max ~4096 chars for WhatsApp)

    Returns:
        Gupshup API response dict
    """
    settings = get_settings()

    if not settings.gupshup_api_key:
        log.warning("Gupshup API key not configured. Skipping WhatsApp message.")
        return {"status": "skipped", "reason": "no_api_key"}

    # Clean phone number — ensure it has country code, no +
    phone = phone.strip().replace("+", "").replace(" ", "").replace("-", "")
    if not phone.startswith("91") and len(phone) == 10:
        phone = f"91{phone}"

    url = "https://api.gupshup.io/wa/api/v1/msg"
    headers = {
        "apikey": settings.gupshup_api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "channel": "whatsapp",
        "source": settings.gupshup_source_number,
        "destination": phone,
        "message": f'{{"type": "text", "text": "{_escape_json(message)}"}}',
        "src.name": settings.gupshup_app_name,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, data=data)
            result = response.json()

            if response.status_code == 200 and result.get("status") == "submitted":
                log.info(f"WhatsApp sent to {phone[:4]}***")
                return {"status": "sent", "message_id": result.get("messageId")}
            else:
                log.error(f"WhatsApp failed for {phone[:4]}***: {result}")
                return {"status": "failed", "error": str(result)}

    except Exception as e:
        log.error(f"WhatsApp send error: {e}")
        return {"status": "error", "error": str(e)}


def _escape_json(text: str) -> str:
    """Escape text for JSON string embedding."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


async def send_whatsapp_template(phone: str, template_id: str, params: list[str]) -> dict:
    """Send a pre-approved WhatsApp template message.

    Use for first-time messages or messages outside 24-hour window.
    Templates must be approved by Meta first.
    """
    settings = get_settings()

    if not settings.gupshup_api_key:
        return {"status": "skipped", "reason": "no_api_key"}

    phone = phone.strip().replace("+", "").replace(" ", "").replace("-", "")
    if not phone.startswith("91") and len(phone) == 10:
        phone = f"91{phone}"

    url = "https://api.gupshup.io/wa/api/v1/template/msg"
    headers = {
        "apikey": settings.gupshup_api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Build template params
    template_params = [{"type": "text", "text": p} for p in params]

    import json
    data = {
        "channel": "whatsapp",
        "source": settings.gupshup_source_number,
        "destination": phone,
        "template": json.dumps({
            "id": template_id,
            "params": template_params,
        }),
        "src.name": settings.gupshup_app_name,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, data=data)
            result = response.json()
            if response.status_code == 200:
                return {"status": "sent", "message_id": result.get("messageId")}
            return {"status": "failed", "error": str(result)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
