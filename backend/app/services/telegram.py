"""Telegram Bot API — send alert messages to users (priority channel)."""

import logging
import httpx
from app.core.config import get_settings

log = logging.getLogger(__name__)


def get_bot_username() -> str | None:
    """Return bot username (without @) for link generation, or None if not configured."""
    settings = get_settings()
    if not settings.telegram_bot_token:
        return None
    try:
        with httpx.Client(timeout=5) as client:
            r = client.get(f"https://api.telegram.org/bot{settings.telegram_bot_token}/getMe")
            if r.status_code == 200 and r.json().get("ok"):
                return r.json().get("result", {}).get("username")
    except Exception as e:
        log.warning("getMe failed: %s", e)
    return None


async def send_telegram_message(chat_id: str, text: str) -> dict:
    """Send a text message to a Telegram chat via Bot API.

    Args:
        chat_id: Telegram chat ID (user gets this when they /start the bot).
        text: Message text (max 4096 chars).

    Returns:
        {"status": "sent"} or {"status": "error", "error": "..."}
    """
    settings = get_settings()
    if not settings.telegram_bot_token:
        log.warning("Telegram bot token not configured. Skipping.")
        return {"status": "skipped", "reason": "no_bot_token"}

    if not chat_id or not str(chat_id).strip():
        return {"status": "skipped", "reason": "no_chat_id"}

    text = (text or "").strip()[:4096]
    if not text:
        return {"status": "skipped", "reason": "empty_message"}

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            if resp.status_code == 200 and data.get("ok"):
                log.info("Telegram sent to chat_id %s", str(chat_id)[:8] + "***")
                return {"status": "sent", "message_id": data.get("result", {}).get("message_id")}
            log.warning("Telegram API error: %s", data)
            return {"status": "failed", "error": data.get("description", str(data))}
    except Exception as e:
        log.error("Telegram send error: %s", e)
        return {"status": "error", "error": str(e)}
