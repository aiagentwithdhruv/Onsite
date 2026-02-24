"""WhatsApp messaging via Meta Cloud API (direct — no BSP middleman).

Endpoint: POST https://graph.facebook.com/v21.0/{phone_number_id}/messages
Auth: Bearer token from Meta Business Manager
"""

import logging
import httpx
from app.core.config import get_settings

log = logging.getLogger(__name__)


def _clean_phone(phone: str) -> str:
    """Ensure phone has country code, no + prefix."""
    phone = phone.strip().replace("+", "").replace(" ", "").replace("-", "")
    if not phone.startswith("91") and len(phone) == 10:
        phone = f"91{phone}"
    return phone


async def send_whatsapp_message(phone: str, message: str, name: str = "") -> dict:
    """Send a WhatsApp text message via Meta Cloud API.

    Args:
        phone: Recipient phone number (e.g., "919876543210")
        message: Text message to send (max ~4096 chars)
        name: Unused (kept for API compatibility)
    """
    settings = get_settings()

    if not settings.whatsapp_cloud_token:
        log.warning("WhatsApp Cloud API token not set. Skipping.")
        return {"status": "skipped", "reason": "no_api_key"}

    if not settings.whatsapp_phone_number_id:
        log.warning("WhatsApp Phone Number ID not set. Skipping.")
        return {"status": "skipped", "reason": "no_phone_number_id"}

    phone = _clean_phone(phone)
    url = f"https://graph.facebook.com/v21.0/{settings.whatsapp_phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {settings.whatsapp_cloud_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {"body": message[:4096]},
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            result = response.json()

            if response.status_code in (200, 201):
                msg_id = ""
                messages = result.get("messages", [])
                if messages:
                    msg_id = messages[0].get("id", "")
                log.info(f"WhatsApp sent to {phone[:4]}*** (id={msg_id})")
                return {"status": "sent", "message_id": msg_id}
            else:
                error = result.get("error", {})
                err_msg = error.get("message", str(result))
                log.error(f"WhatsApp failed for {phone[:4]}***: {response.status_code} {err_msg}")
                return {"status": "failed", "error": err_msg}

    except Exception as e:
        log.error(f"WhatsApp send error: {e}")
        return {"status": "error", "error": str(e)}


async def send_whatsapp_template(
    phone: str,
    template_name: str,
    language_code: str = "en",
    components: list | None = None,
) -> dict:
    """Send a pre-approved template message via Meta Cloud API.

    Use for first-time messages or outside 24-hour window.
    """
    settings = get_settings()

    if not settings.whatsapp_cloud_token or not settings.whatsapp_phone_number_id:
        return {"status": "skipped", "reason": "no_api_key"}

    phone = _clean_phone(phone)
    url = f"https://graph.facebook.com/v21.0/{settings.whatsapp_phone_number_id}/messages"

    template_obj = {
        "name": template_name,
        "language": {"code": language_code},
    }
    if components:
        template_obj["components"] = components

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": template_obj,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.whatsapp_cloud_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            result = response.json()
            if response.status_code in (200, 201):
                messages = result.get("messages", [])
                msg_id = messages[0].get("id", "") if messages else ""
                return {"status": "sent", "message_id": msg_id}
            error = result.get("error", {})
            return {"status": "failed", "error": error.get("message", str(result))}
    except Exception as e:
        return {"status": "error", "error": str(e)}
