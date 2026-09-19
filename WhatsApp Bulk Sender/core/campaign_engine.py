"""
Campaign Execution Engine & State Machine (core/campaign_engine.py)
Implements full campaign lifecycle: Draft -> Scheduled -> Running -> Paused -> Completed / Failed,
Spintax evaluation, dynamic personalization, anti-ban throttling, and multi-provider dispatch.
"""

import time
import random
import re
from datetime import datetime
from core.db import get_connection
from core.audit import log_audit
from core.whatsapp.selenium_driver import SeleniumChromeProvider


def parse_spintax(text):
    """Recursively evaluates spintax {opt1|opt2|opt3} into randomized selection."""
    if not text:
        return ""
    pattern = r"\{([^{}]+)\}"
    while re.search(pattern, text):
        def repl(m):
            return random.choice(m.group(1).split("|"))
        text = re.sub(pattern, repl, text)
    return text


def create_campaign(name, template_id=None, scheduled_at=None, min_delay=8, max_delay=15, recipient_list=None, org_id=1):
    """Creates a new campaign and stages its recipient list."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "Scheduled" if scheduled_at else "Draft"
    count = len(recipient_list or [])

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO campaigns (org_id, name, status, template_id, scheduled_at, min_delay, max_delay, total_recipients, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (org_id, name.strip(), status, template_id, scheduled_at, min_delay, max_delay, count, now, now))
        campaign_id = cursor.lastrowid

        if recipient_list:
            for r in recipient_list:
                phone = r.get("phone", "")
                c_name = r.get("name", "Customer")
                c_id = r.get("id", None)
                cursor.execute("""
                    INSERT INTO campaign_recipients (campaign_id, contact_id, phone, name, status)
                    VALUES (?, ?, ?, ?, 'PENDING')
                """, (campaign_id, c_id, phone, c_name))

        conn.commit()
        log_audit("System", f"Created campaign '{name}'", target_type="Campaign", target_id=campaign_id)
        return campaign_id


def get_all_campaigns(status_filter=None):
    """Returns list of campaigns with progress metrics."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if status_filter and status_filter != "All Statuses":
            cursor.execute("""
                SELECT c.id, c.name, c.status, c.scheduled_at, c.total_recipients, c.sent_count, c.failed_count, c.created_at, t.title as template_title
                FROM campaigns c
                LEFT JOIN templates t ON c.template_id = t.id
                WHERE c.status = ?
                ORDER BY c.id DESC
            """, (status_filter,))
        else:
            cursor.execute("""
                SELECT c.id, c.name, c.status, c.scheduled_at, c.total_recipients, c.sent_count, c.failed_count, c.created_at, t.title as template_title
                FROM campaigns c
                LEFT JOIN templates t ON c.template_id = t.id
                ORDER BY c.id DESC
            """)
        return [dict(r) for r in cursor.fetchall()]


def update_campaign_status(campaign_id, status):
    """Updates campaign status (Draft, Scheduled, Running, Paused, Completed, Failed)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE campaigns SET status = ?, updated_at = ? WHERE id = ?", (status, now, campaign_id))
        conn.commit()


def get_campaign_recipients(campaign_id):
    """Fetches full recipient list for execution."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, phone, name, status, sent_at, error_message FROM campaign_recipients WHERE campaign_id = ?", (campaign_id,))
        return [dict(r) for r in cursor.fetchall()]


def update_recipient_status(recipient_id, status, error_msg=""):
    """Updates status for a single recipient."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE campaign_recipients
            SET status = ?, sent_at = ?, error_message = ?
            WHERE id = ?
        """, (status, now, error_msg, recipient_id))
        conn.commit()


def sync_campaign_counters(campaign_id):
    """Synchronizes sent_count and failed_count on the campaign record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM campaign_recipients WHERE campaign_id = ? AND status = 'SENT'", (campaign_id,))
        sent = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM campaign_recipients WHERE campaign_id = ? AND status IN ('FAILED', 'SKIPPED')", (campaign_id,))
        failed = cursor.fetchone()[0] or 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE campaigns SET sent_count = ?, failed_count = ?, updated_at = ? WHERE id = ?", (sent, failed, now, campaign_id))
        conn.commit()


def recover_interrupted_campaigns():
    """
    On application boot or crash recovery, detects any campaigns stuck in 'Running' state
    and safely pauses them with audit log, so the user can inspect or resume without data loss.
    Returns the number of campaigns recovered.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    recovered = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM campaigns WHERE status = 'Running'")
        stuck = cursor.fetchall()
        if not stuck:
            return 0

        for row in stuck:
            c_id = row[0]
            c_name = row[1]
            cursor.execute("UPDATE campaigns SET status = 'Paused', updated_at = ? WHERE id = ?", (now, c_id))
            recovered.append((c_id, c_name))
        conn.commit()

    for c_id, c_name in recovered:
        log_audit("System", f"Auto-recovered interrupted campaign '{c_name}' (ID: {c_id}) from Running to Paused.", target_type="Campaign", target_id=c_id)

    return len(recovered)
