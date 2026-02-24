"""Discord webhook — send alert messages to a user's Discord channel."""

import logging
import httpx

log = logging.getLogger(__name__)


async def send_discord_webhook(webhook_url: str, content: str) -> dict:
    """Send a message to a Discord channel via webhook URL.

    User creates a webhook in their Discord server (Channel Settings → Integrations → Webhooks)
    and pastes the URL here. Alerts are posted to that channel.

    Args:
        webhook_url: Full Discord webhook URL (https://discord.com/api/webhooks/...).
        content: Message text (Discord limit 2000 chars).

    Returns:
        {"status": "sent"} or {"status": "error", "error": "..."}
    """
    if not webhook_url or not webhook_url.strip():
        return {"status": "skipped", "reason": "no_webhook_url"}

    webhook_url = webhook_url.strip()
    if not webhook_url.startswith("https://discord.com/api/webhooks/") and not webhook_url.startswith("https://discordapp.com/api/webhooks/"):
        return {"status": "skipped", "reason": "invalid_webhook_url"}

    content = (content or "").strip()[:2000]
    if not content:
        return {"status": "skipped", "reason": "empty_message"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(webhook_url, json={"content": content})
            if r.status_code in (200, 204):
                log.info("Discord webhook sent")
                return {"status": "sent"}
            log.warning("Discord webhook failed: %s %s", r.status_code, r.text[:200])
            return {"status": "failed", "error": r.text[:200] or str(r.status_code)}
    except Exception as e:
        log.error("Discord send error: %s", e)
        return {"status": "error", "error": str(e)}
