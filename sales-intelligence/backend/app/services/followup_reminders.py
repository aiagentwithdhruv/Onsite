"""Follow-up reminder service — checks for due follow-ups and notifies reps.

Runs every 15 minutes via scheduler. Sends reminders:
  - 15 min before follow-up time → "Upcoming: Call {lead} in 15 min"
  - At follow-up time → "NOW: Call {lead} — {remarks}"
  - Overdue (missed by 1+ hour) → "OVERDUE: {lead} follow-up was at {time}"
  - Morning summary (8 AM) → "Today's follow-ups: {list}"

Delivery: Telegram (priority) → WhatsApp → Email (same as alert_delivery.py)
"""

import logging
from datetime import datetime, timezone, timedelta, date, time as dt_time

from app.core.supabase_client import get_supabase_admin

log = logging.getLogger(__name__)

# IST offset (UTC+5:30)
IST_OFFSET = timedelta(hours=5, minutes=30)


def _now_ist() -> datetime:
    """Current time in IST."""
    return datetime.now(timezone.utc) + IST_OFFSET


def _format_reminder(lead: dict, reminder_type: str) -> str:
    """Format a follow-up reminder message for Telegram/WhatsApp."""
    name = lead.get("contact_name") or lead.get("company") or "Unknown Lead"
    company = lead.get("company") or ""
    phone = lead.get("phone") or ""
    remarks = lead.get("remarks") or lead.get("follow_up_note") or ""
    fu_time = lead.get("follow_up_time") or ""
    stage = lead.get("stage") or ""

    # Format time nicely
    time_str = ""
    if fu_time:
        try:
            t = datetime.strptime(str(fu_time)[:5], "%H:%M")
            time_str = t.strftime("%I:%M %p")
        except Exception:
            time_str = str(fu_time)

    sep = "─────────────────"

    if reminder_type == "15min_before":
        lines = [
            "📬 ONSITE",
            sep,
            f"⏰ UPCOMING (15 min)",
            sep,
            f"📞 Call: {name}",
        ]
        if company:
            lines.append(f"🏢 {company}")
        if time_str:
            lines.append(f"🕐 At {time_str}")
        if phone:
            lines.append(f"📱 {phone}")
        if remarks:
            lines.append(f"📝 {remarks}")

    elif reminder_type == "at_time":
        lines = [
            "📬 ONSITE",
            sep,
            f"🔴 CALL NOW",
            sep,
            f"📞 {name}",
        ]
        if company:
            lines.append(f"🏢 {company}")
        if phone:
            lines.append(f"📱 {phone}")
        if stage:
            lines.append(f"📊 Stage: {stage}")
        if remarks:
            lines.append("")
            lines.append(f"📝 {remarks}")

    elif reminder_type == "overdue":
        lines = [
            "📬 ONSITE",
            sep,
            f"⚠️ OVERDUE FOLLOW-UP",
            sep,
            f"📞 {name}",
        ]
        if company:
            lines.append(f"🏢 {company}")
        if time_str:
            lines.append(f"🕐 Was scheduled at {time_str}")
        if phone:
            lines.append(f"📱 {phone}")
        if remarks:
            lines.append(f"📝 {remarks}")
        lines.append("")
        lines.append("Please call ASAP or reschedule.")

    else:  # morning_summary handled separately
        lines = [f"Follow-up: {name} ({company})"]

    return "\n".join(lines)


def _format_morning_summary(leads: list[dict]) -> str:
    """Format the morning summary of all today's follow-ups."""
    sep = "─────────────────"
    lines = [
        "📬 ONSITE",
        "📋 Today's Follow-Ups",
        sep,
        f"You have {len(leads)} follow-up(s) today.",
        "",
    ]

    for i, lead in enumerate(leads, 1):
        name = lead.get("contact_name") or lead.get("company") or "Unknown"
        fu_time = lead.get("follow_up_time") or ""
        time_str = ""
        if fu_time:
            try:
                t = datetime.strptime(str(fu_time)[:5], "%H:%M")
                time_str = t.strftime("%I:%M %p")
            except Exception:
                time_str = str(fu_time)

        phone = lead.get("phone") or ""
        remarks = lead.get("remarks") or lead.get("follow_up_note") or ""

        line = f"{i}. {name}"
        if time_str:
            line += f" — {time_str}"
        if phone:
            line += f" ({phone})"
        lines.append(line)
        if remarks:
            lines.append(f"   📝 {remarks}")

    lines.append("")
    lines.append(sep)
    lines.append("Good luck today! 💪")
    return "\n".join(lines)


async def _send_reminder(user: dict, message: str, lead: dict, reminder_type: str, db):
    """Send reminder to a user via their preferred channels."""
    from app.services.alert_delivery import deliver_message_to_user

    result = await deliver_message_to_user(user, message, subject="Follow-Up Reminder")

    # Log the reminder
    try:
        lead_id = lead.get("id")
        sent_via = "none"
        for ch in ("telegram", "whatsapp", "email"):
            if (result.get(ch) or {}).get("status") == "sent":
                sent_via = ch
                break

        if lead_id:
            db.table("follow_up_reminders").insert({
                "lead_id": lead_id,
                "user_id": user.get("id"),
                "follow_up_date": lead.get("follow_up_date"),
                "follow_up_time": lead.get("follow_up_time"),
                "reminder_type": reminder_type,
                "sent_via": sent_via,
            }).execute()
    except Exception as e:
        log.debug(f"Could not log reminder: {e}")

    return result


async def check_and_send_reminders():
    """Main function — called every 15 minutes by scheduler.

    Checks for follow-ups due in the next window and sends reminders.
    """
    db = get_supabase_admin()
    if not db:
        log.warning("Follow-up reminders: DB unavailable")
        return {"sent": 0, "errors": []}

    now = _now_ist()
    today = now.date().isoformat()
    current_time = now.strftime("%H:%M")

    # Window: check follow-ups in the next 20 minutes and overdue by up to 2 hours
    window_start = (now - timedelta(hours=2)).strftime("%H:%M")
    window_end = (now + timedelta(minutes=20)).strftime("%H:%M")

    sent = 0
    errors = []

    try:
        # Get all leads with follow-ups due today that haven't been reminded
        result = db.table("leads").select(
            "id, zoho_lead_id, contact_name, company, phone, email, stage, "
            "follow_up_date, follow_up_time, follow_up_note, follow_up_reminded, "
            "remarks, deal_owner, assigned_rep_id"
        ).eq("follow_up_date", today).eq("follow_up_reminded", False).execute()

        leads_due = result.data or []
        if not leads_due:
            return {"sent": 0, "checked": 0}

        log.info(f"Follow-up reminders: {len(leads_due)} leads due today")

        # Get users for notification
        rep_ids = list({l["assigned_rep_id"] for l in leads_due if l.get("assigned_rep_id")})
        users_map = {}
        if rep_ids:
            users_result = db.table("users").select(
                "id, email, name, phone, telegram_chat_id, "
                "notify_via_telegram, notify_via_whatsapp, notify_via_email, "
                "discord_webhook_url, notify_via_discord"
            ).in_("id", rep_ids).execute()
            users_map = {u["id"]: u for u in (users_result.data or [])}

        # Also get users by deal_owner name for unassigned leads
        deal_owners = list({l["deal_owner"] for l in leads_due if l.get("deal_owner") and not l.get("assigned_rep_id")})
        if deal_owners:
            for owner_name in deal_owners:
                owner_result = db.table("users").select(
                    "id, email, name, phone, telegram_chat_id, "
                    "notify_via_telegram, notify_via_whatsapp, notify_via_email, "
                    "discord_webhook_url, notify_via_discord, deal_owner_name"
                ).eq("deal_owner_name", owner_name).maybe_single().execute()
                if owner_result and owner_result.data:
                    users_map[owner_result.data["id"]] = owner_result.data

        for lead in leads_due:
            fu_time = lead.get("follow_up_time")
            fu_time_str = str(fu_time)[:5] if fu_time else None

            # Determine which user to notify
            user = None
            if lead.get("assigned_rep_id") and lead["assigned_rep_id"] in users_map:
                user = users_map[lead["assigned_rep_id"]]
            elif lead.get("deal_owner"):
                # Find user by deal_owner name
                for u in users_map.values():
                    if u.get("deal_owner_name") == lead["deal_owner"]:
                        user = u
                        break

            if not user:
                log.debug(f"No user found for lead {lead.get('contact_name')} (owner: {lead.get('deal_owner')})")
                continue

            # Determine reminder type based on current time vs follow-up time
            reminder_type = None

            if not fu_time_str:
                # No specific time — send at 9 AM IST as "at_time"
                if "08:45" <= current_time <= "09:15":
                    reminder_type = "at_time"
            else:
                # Has specific time
                try:
                    fu_minutes = int(fu_time_str[:2]) * 60 + int(fu_time_str[3:5])
                    now_minutes = now.hour * 60 + now.minute

                    diff = fu_minutes - now_minutes

                    if 10 <= diff <= 20:
                        reminder_type = "15min_before"
                    elif -5 <= diff <= 5:
                        reminder_type = "at_time"
                    elif -120 <= diff < -60:
                        reminder_type = "overdue"
                except Exception:
                    # Can't parse time, treat as at_time in morning
                    if "08:45" <= current_time <= "09:15":
                        reminder_type = "at_time"

            if not reminder_type:
                continue

            # Check if this specific reminder was already sent
            try:
                existing = db.table("follow_up_reminders").select("id").eq(
                    "lead_id", lead["id"]
                ).eq("follow_up_date", today).eq(
                    "reminder_type", reminder_type
                ).maybe_single().execute()
                if existing and existing.data:
                    continue  # Already sent this reminder type today
            except Exception:
                pass  # Table might not exist yet

            # Send the reminder
            try:
                message = _format_reminder(lead, reminder_type)
                await _send_reminder(user, message, lead, reminder_type, db)
                sent += 1
                log.info(f"Sent {reminder_type} reminder for {lead.get('contact_name')} to {user.get('name')}")

                # Mark as reminded if it's the "at_time" or "overdue" reminder
                if reminder_type in ("at_time", "overdue"):
                    db.table("leads").update(
                        {"follow_up_reminded": True}
                    ).eq("id", lead["id"]).execute()

            except Exception as e:
                log.error(f"Failed to send reminder for {lead.get('contact_name')}: {e}")
                errors.append(str(e))

    except Exception as e:
        if "does not exist" in str(e) or "Could not find" in str(e):
            log.warning("Follow-up columns not migrated yet. Run migration 013_followup_fields.sql")
            return {"sent": 0, "error": "migration_needed"}
        log.error(f"Follow-up reminder check failed: {e}")
        errors.append(str(e))

    log.info(f"Follow-up reminders: sent {sent}, errors {len(errors)}")
    return {"sent": sent, "errors": errors}


async def send_morning_followup_summary():
    """Send each rep a summary of their follow-ups for today. Called at 8 AM IST."""
    db = get_supabase_admin()
    if not db:
        return {"sent": 0}

    today = date.today().isoformat()
    sent = 0

    try:
        # Get all today's follow-ups
        result = db.table("leads").select(
            "id, contact_name, company, phone, follow_up_date, follow_up_time, "
            "follow_up_note, remarks, deal_owner, assigned_rep_id, stage"
        ).eq("follow_up_date", today).order("follow_up_time").execute()

        leads_today = result.data or []
        if not leads_today:
            return {"sent": 0, "leads_today": 0}

        # Group by assigned rep
        from collections import defaultdict
        by_rep: dict[str, list] = defaultdict(list)

        for lead in leads_today:
            rep_id = lead.get("assigned_rep_id")
            if rep_id:
                by_rep[rep_id].append(lead)

        # Get users
        rep_ids = list(by_rep.keys())
        if not rep_ids:
            return {"sent": 0, "leads_today": len(leads_today), "no_assigned_rep": True}

        users_result = db.table("users").select(
            "id, email, name, phone, telegram_chat_id, "
            "notify_via_telegram, notify_via_whatsapp, notify_via_email, "
            "discord_webhook_url, notify_via_discord"
        ).in_("id", rep_ids).execute()
        users_map = {u["id"]: u for u in (users_result.data or [])}

        for rep_id, rep_leads in by_rep.items():
            user = users_map.get(rep_id)
            if not user:
                continue

            message = _format_morning_summary(rep_leads)
            from app.services.alert_delivery import deliver_message_to_user
            await deliver_message_to_user(user, message, subject="Today's Follow-Ups")
            sent += 1

        log.info(f"Morning follow-up summary: sent to {sent} reps, {len(leads_today)} follow-ups today")

    except Exception as e:
        if "does not exist" in str(e) or "Could not find" in str(e):
            log.warning("Follow-up columns not migrated. Run 013_followup_fields.sql")
            return {"sent": 0, "error": "migration_needed"}
        log.error(f"Morning follow-up summary failed: {e}")

    return {"sent": sent}
