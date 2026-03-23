"""Gallabox WhatsApp sender — text + template messages."""

import json
import urllib.request
from config import GALLABOX_API_KEY, GALLABOX_API_SECRET, GALLABOX_CHANNEL_ID, GALLABOX_URL


def send_template(phone: str, name: str = "Team") -> dict:
    payload = {
        "channelId": GALLABOX_CHANNEL_ID,
        "channelType": "whatsapp",
        "recipient": {"name": name, "phone": phone},
        "whatsapp": {
            "type": "template",
            "template": {"templateName": "onsite_morning_kickoff", "bodyValues": {"1": name}},
        },
    }
    return _post(payload)


def send_text(phone: str, message: str, name: str = "Team") -> dict:
    if len(message) > 4096:
        message = message[:4090] + "\n..."
    payload = {
        "channelId": GALLABOX_CHANNEL_ID,
        "channelType": "whatsapp",
        "recipient": {"name": name, "phone": phone},
        "whatsapp": {"type": "text", "text": {"body": message}},
    }
    return _post(payload)


def send_to_team(team: dict, message_fn, template_first: bool = False) -> dict:
    """Send personalized messages to a team dict {name: phone}.
    message_fn(name) should return the message string.
    """
    results = {}
    for name, phone in team.items():
        if template_first:
            send_template(phone, name)
        msg = message_fn(name)
        if msg:
            r = send_text(phone, msg, name)
            status = r.get("status", "FAILED")
            results[name] = status
            print(f"  {'OK' if status == 'ACCEPTED' else 'FAIL'} -> {name} ({phone})")
        else:
            results[name] = "SKIPPED"
    return results


def _post(payload: dict) -> dict:
    headers = {
        "apiKey": GALLABOX_API_KEY,
        "apiSecret": GALLABOX_API_SECRET,
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(GALLABOX_URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"status": "FAILED", "error": str(e), "body": body}
