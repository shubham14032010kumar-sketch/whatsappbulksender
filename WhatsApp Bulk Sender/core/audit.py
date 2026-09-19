"""
Audit Logging System (core/audit.py)
Tracks all critical business operations: Who, What, When, and Target Details.
"""

from datetime import datetime
from core.db import get_connection


def log_audit(user_name="System", action="", target_type="", target_id="", details="", org_id=1, user=None):
    """Inserts a persistent audit entry."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name_str = "System"
    if user:
        if isinstance(user, dict):
            name_str = user.get("name") or user.get("email") or "System"
        else:
            name_str = str(user)
    elif user_name:
        if isinstance(user_name, dict):
            name_str = user_name.get("name") or user_name.get("email") or "System"
        else:
            name_str = str(user_name)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (org_id, user_name, action, target_type, target_id, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (org_id, name_str, str(action), str(target_type), str(target_id), str(details), now))
        conn.commit()


def get_audit_logs(limit=200, offset=0, filter_action=None):
    """Fetches chronological audit logs."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if filter_action and filter_action.strip():
            cursor.execute("""
                SELECT id, user_name, action, target_type, target_id, details, timestamp
                FROM audit_logs
                WHERE action LIKE ?
                ORDER BY id DESC LIMIT ? OFFSET ?
            """, (f"%{filter_action.strip()}%", limit, offset))
        else:
            cursor.execute("""
                SELECT id, user_name, action, target_type, target_id, details, timestamp
                FROM audit_logs
                ORDER BY id DESC LIMIT ? OFFSET ?
            """, (limit, offset))
        return [dict(r) for r in cursor.fetchall()]
