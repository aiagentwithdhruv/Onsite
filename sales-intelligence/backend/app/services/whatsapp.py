"""WhatsApp messaging — Gallabox (primary) + Meta Cloud API (fallback).

Priority: If Gallabox keys are set → use Gallabox.
          Else if Meta Cloud API keys are set → use Meta direct.
          Else → skip.

Template fallback: Outside the 24-hour window, free-form text messages
fail silently on WhatsApp. We auto-fallback to a pre-approved template
message when text delivery fails or when explicitly requested.
"""

import logging
import httpx
from app.core.config import get_settings

log = logging.getLogger(__name__)

# Default template for notifications (must exist in Gallabox/WABA)
# "sample_template" is Meta's default template that every WABA account has.
# TODO: Create custom "onsite_alert" template in Gallabox dashboard for
#       richer notifications with variables (body: "{{1}}")
DEFAULT_GALLABOX_TEMPLATE = "sample_template"


def _clean_phone(phone: str) -> str:
    """Ensure phone has country code, no + prefix."""
    phone = phone.strip().replace("+", "").replace(" ", "").replace("-", "")
    if not phone.startswith("91") and len(phone) == 10:
        phone = f"91{phone}"
    return phone


def _gallabox_headers() -> dict:
    """Common Gallabox API headers."""
    settings = get_settings()
    return {
        "apiKey": settings.gallabox_api_key,
        "apiSecret": settings.gallabox_api_secret,
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Gallabox API — Text messages
# Docs: https://documenter.getpostman.com/view/19289684/2s93JtP3FZ
# ---------------------------------------------------------------------------

async def _send_via_gallabox(phone: str, message: str, name: str = "Team Member") -> dict:
    """Send text message via Gallabox API."""
    settings = get_settings()
    url = "https://server.gallabox.com/devapi/messages/whatsapp"

    payload = {
        "channelId": settings.gallabox_channel_id,
        "channelType": "whatsapp",
        "recipient": {"name": name or "Team Member", "phone": phone},
        "whatsapp": {
            "type": "text",
            "text": {"body": message[:4096]},
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=_gallabox_headers(), json=payload)
            result = response.json()

            if response.status_code in (200, 201, 202):
                msg_id = result.get("id", result.get("messageId", ""))
                log.info(f"WhatsApp (Gallabox/text) sent to {phone[:4]}*** (id={msg_id})")
                return {"status": "sent", "message_id": str(msg_id), "provider": "gallabox", "type": "text"}
            else:
                err_msg = result.get("message", str(result))
                log.warning(f"WhatsApp (Gallabox/text) failed for {phone[:4]}***: {response.status_code} {err_msg}")
                return {"status": "failed", "error": err_msg, "provider": "gallabox", "type": "text"}

    except Exception as e:
        log.error(f"WhatsApp (Gallabox/text) error: {e}")
        return {"status": "error", "error": str(e), "provider": "gallabox", "type": "text"}


# ---------------------------------------------------------------------------
# Gallabox API — Template messages (works outside 24-hour window)
# ---------------------------------------------------------------------------

async def _send_template_via_gallabox(
    phone: str,
    template_name: str,
    body_values: dict | None = None,
    name: str = "Team Member",
) -> dict:
    """Send a pre-approved template message via Gallabox API.

    Args:
        phone: Recipient phone (with country code, no +)
        template_name: Name of the approved template in Gallabox
        body_values: Dict of placeholder values, e.g. {"1": "Hello Dhruv"}
        name: Recipient display name
    """
    settings = get_settings()
    url = "https://server.gallabox.com/devapi/messages/whatsapp"

    template_obj: dict = {"templateName": template_name}
    if body_values:
        template_obj["bodyValues"] = body_values

    payload = {
        "channelId": settings.gallabox_channel_id,
        "channelType": "whatsapp",
        "recipient": {"name": name or "Team Member", "phone": phone},
        "whatsapp": {
            "type": "template",
            "template": template_obj,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=_gallabox_headers(), json=payload)
            result = response.json()

            if response.status_code in (200, 201, 202):
                msg_id = result.get("id", result.get("messageId", ""))
                log.info(f"WhatsApp (Gallabox/template:{template_name}) sent to {phone[:4]}*** (id={msg_id})")
                return {"status": "sent", "message_id": str(msg_id), "provider": "gallabox", "type": "template", "template": template_name}
            else:
                err_msg = result.get("message", str(result))
                log.error(f"WhatsApp (Gallabox/template:{template_name}) failed for {phone[:4]}***: {response.status_code} {err_msg}")
                return {"status": "failed", "error": err_msg, "provider": "gallabox", "type": "template"}

    except Exception as e:
        log.error(f"WhatsApp (Gallabox/template) error: {e}")
        return {"status": "error", "error": str(e), "provider": "gallabox", "type": "template"}


# ---------------------------------------------------------------------------
# Meta Cloud API (direct)
# Endpoint: POST https://graph.facebook.com/v21.0/{phone_number_id}/messages
# ---------------------------------------------------------------------------

async def _send_via_meta(phone: str, message: str) -> dict:
    """Send text message via Meta Cloud API."""
    settings = get_settings()
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
                log.info(f"WhatsApp (Meta) sent to {phone[:4]}*** (id={msg_id})")
                return {"status": "sent", "message_id": msg_id, "provider": "meta"}
            else:
                error = result.get("error", {})
                err_msg = error.get("message", str(result))
                log.error(f"WhatsApp (Meta) failed for {phone[:4]}***: {response.status_code} {err_msg}")
                return {"status": "failed", "error": err_msg, "provider": "meta"}

    except Exception as e:
        log.error(f"WhatsApp (Meta) error: {e}")
        return {"status": "error", "error": str(e), "provider": "meta"}


# ---------------------------------------------------------------------------
# Public API — auto-selects provider
# ---------------------------------------------------------------------------

def _get_provider() -> str | None:
    """Determine which WhatsApp provider to use."""
    settings = get_settings()
    if settings.gallabox_api_key and settings.gallabox_api_secret and settings.gallabox_channel_id:
        return "gallabox"
    if settings.whatsapp_cloud_token and settings.whatsapp_phone_number_id:
        return "meta"
    return None


async def send_whatsapp_message(
    phone: str,
    message: str,
    name: str = "",
    use_template: bool = True,
) -> dict:
    """Send a WhatsApp message. Auto-selects Gallabox or Meta Cloud API.

    For Gallabox with use_template=True (default): sends a template message
    first (works outside 24h window), then falls back to text if template fails.
    With use_template=False: sends text only (only works within 24h window).

    Args:
        phone: Recipient phone number (e.g., "919876543210")
        message: Text message to send (max ~4096 chars)
        name: Recipient name for Gallabox
        use_template: If True, prefer template message (default, works anytime)
    """
    provider = _get_provider()

    if not provider:
        log.warning("No WhatsApp provider configured. Skipping.")
        return {"status": "skipped", "reason": "no_api_key"}

    phone = _clean_phone(phone)

    if provider == "gallabox":
        if use_template:
            # Template first (guaranteed delivery outside 24h window)
            tmpl_result = await _send_template_via_gallabox(
                phone,
                template_name=DEFAULT_GALLABOX_TEMPLATE,
                name=name,
            )
            if tmpl_result.get("status") == "sent":
                return tmpl_result
            # Template failed (maybe not approved yet) — fallback to text
            log.info(f"Gallabox template failed, falling back to text for {phone[:4]}***")

        result = await _send_via_gallabox(phone, message, name=name)
        return result
    else:
        return await _send_via_meta(phone, message)


async def send_whatsapp_template(
    phone: str,
    template_name: str,
    language_code: str = "en",
    components: list | None = None,
    body_values: dict | None = None,
    name: str = "",
) -> dict:
    """Send a pre-approved template message. Auto-selects Gallabox or Meta.

    Args:
        phone: Recipient phone number
        template_name: Name of approved template
        language_code: Language code (Meta only, default "en")
        components: Template components (Meta only)
        body_values: Template body values dict (Gallabox only, e.g. {"1": "value"})
        name: Recipient name (Gallabox only)
    """
    provider = _get_provider()
    phone = _clean_phone(phone)

    # Try Gallabox first
    if provider == "gallabox":
        return await _send_template_via_gallabox(
            phone, template_name, body_values=body_values, name=name,
        )

    # Meta Cloud API
    settings = get_settings()
    if not settings.whatsapp_cloud_token or not settings.whatsapp_phone_number_id:
        return {"status": "skipped", "reason": "no_api_key"}

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
                return {"status": "sent", "message_id": msg_id, "provider": "meta", "type": "template"}
            error = result.get("error", {})
            return {"status": "failed", "error": error.get("message", str(result)), "provider": "meta"}
    except Exception as e:
        return {"status": "error", "error": str(e), "provider": "meta"}
