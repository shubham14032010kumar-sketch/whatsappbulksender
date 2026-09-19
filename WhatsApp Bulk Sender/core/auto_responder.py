"""
2-Way Auto-Responder & Inbound Lead Agent (core/auto_responder.py)
Automates 24/7 customer engagement:
1. Matches incoming customer queries against configured keywords
2. Automatically generates instant replies (Pricing, Catalog, Location, Demo)
3. Detects high-intent interest ("interested", "buy", "call", "demo") and tags contact as 'HOT LEAD'
4. Integrates with SQLite auto_reply_rules and CRM contact store
"""

import re
from datetime import datetime
from core.db import get_connection
from core.audit import log_audit

DEFAULT_RULES = [
    {
        "keyword": "price, rate, cost, fees, fee, pricing",
        "match_type": "CONTAINS",
        "reply_text": "Hello! Thank you for inquiring. Here is our complete pricing brochure & package details. Our team is available if you would like a custom quote!",
        "tag_lead": "WARM_LEAD"
    },
    {
        "keyword": "interested, demo, call me, want to buy, yes, book, admission",
        "match_type": "CONTAINS",
        "reply_text": "Thank you for your interest! Your inquiry has been prioritized. Our executive will call you within 15 minutes to assist you with complete details.",
        "tag_lead": "HOT_LEAD"
    },
    {
        "keyword": "location, address, venue, kahan hai, office",
        "match_type": "CONTAINS",
        "reply_text": "Our office is centrally located. You can visit us Mon-Sat between 10 AM to 7 PM. Let us know if you need Google Maps navigation!",
        "tag_lead": "LOCATION_INQUIRY"
    },
    {
        "keyword": "stop, unsubscribe, mat bhejo, remove",
        "match_type": "CONTAINS",
        "reply_text": "We have recorded your preference and removed your number from promotional broadcasts. Have a great day ahead!",
        "tag_lead": "OPT_OUT"
    }
]

def init_auto_responder_table():
    """Ensures auto_reply_rules table exists and is seeded with defaults."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auto_reply_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                match_type TEXT DEFAULT 'CONTAINS', -- CONTAINS, EXACT, REGEX
                reply_text TEXT NOT NULL,
                media_path TEXT,
                tag_lead TEXT DEFAULT 'WARM_LEAD',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        
        # Check if rules are seeded
        cursor.execute("SELECT COUNT(*) FROM auto_reply_rules")
        count = cursor.fetchone()[0]
        if count == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for r in DEFAULT_RULES:
                cursor.execute("""
                    INSERT INTO auto_reply_rules (keyword, match_type, reply_text, tag_lead, is_active, created_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (r["keyword"], r["match_type"], r["reply_text"], r["tag_lead"], now))
            conn.commit()

def get_all_rules():
    """Returns all configured auto-reply rules."""
    init_auto_responder_table()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM auto_reply_rules ORDER BY id ASC")
        return [dict(r) for r in cursor.fetchall()]

def add_rule(keyword, reply_text, match_type="CONTAINS", tag_lead="HOT_LEAD", media_path=None):
    """Adds a new auto-reply rule."""
    init_auto_responder_table()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO auto_reply_rules (keyword, match_type, reply_text, media_path, tag_lead, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (keyword.strip(), match_type, reply_text.strip(), media_path, tag_lead, now))
        conn.commit()
        rule_id = cursor.lastrowid
        log_audit("AutoResponder", f"Added auto-reply rule for '{keyword}'", target_type="Rule", target_id=rule_id)
        return rule_id

def delete_rule(rule_id):
    """Deletes an auto-reply rule by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM auto_reply_rules WHERE id = ?", (rule_id,))
        conn.commit()
        log_audit("AutoResponder", f"Deleted auto-reply rule ID {rule_id}")

def toggle_rule(rule_id, is_active):
    """Activates or deactivates a rule."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE auto_reply_rules SET is_active = ? WHERE id = ?", (1 if is_active else 0, rule_id))
        conn.commit()

def process_incoming_message(phone, text):
    """
    Evaluates an incoming message against active rules.
    If matched:
    - Returns (matched: bool, reply_text: str, tag_lead: str, media_path: str)
    - Automatically updates contact status / tags in CRM if high intent
    """
    init_auto_responder_table()
    clean_text = str(text or "").strip().lower()
    if not clean_text:
        return False, None, None, None

    rules = get_all_rules()
    for rule in rules:
        if not rule.get("is_active"):
            continue

        keywords = [k.strip().lower() for k in rule["keyword"].split(",") if k.strip()]
        match_type = rule.get("match_type", "CONTAINS")
        matched = False

        if match_type == "EXACT":
            matched = any(clean_text == kw for kw in keywords)
        elif match_type == "REGEX":
            matched = any(re.search(kw, clean_text) for kw in keywords)
        else: # CONTAINS
            matched = any(kw in clean_text for kw in keywords)

        if matched:
            tag = rule.get("tag_lead", "WARM_LEAD")
            reply = rule.get("reply_text", "")
            media = rule.get("media_path", None)

            # Auto-update CRM contact tag if phone is provided
            if phone:
                _update_contact_lead_tag(phone, tag)

            log_audit("AutoResponder", f"Auto-reply triggered for '{clean_text}' from {phone} (Tag: {tag})")
            return True, reply, tag, media

    return False, None, None, None

def _update_contact_lead_tag(phone, tag):
    """Internal helper to mark contact as HOT_LEAD / WARM_LEAD in CRM database."""
    clean_ph = re.sub(r"[^\d]", "", str(phone or ""))
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, tags, status FROM contacts WHERE phone LIKE ?", (f"%{clean_ph[-10:]}",))
        row = cursor.fetchone()
        if row:
            cid = row[0]
            curr_tags = row[1] or ""
            if tag not in curr_tags:
                new_tags = f"{curr_tags},{tag}".strip(",")
                new_status = "HOT LEAD" if tag == "HOT_LEAD" else "Active"
                cursor.execute("UPDATE contacts SET tags = ?, status = ? WHERE id = ?", (new_tags, new_status, cid))
                conn.commit()
