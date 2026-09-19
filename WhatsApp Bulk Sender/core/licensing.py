"""
Licensing & Subscription Entitlement System (core/licensing.py)
Provides hardware binding, HMAC signature verification, plan entitlements,
and commercial key activation (supports LICENSE-XXXX-XXXX-XXXX & WBS formats).
"""

import os
import sys
import hmac
import hashlib
import uuid
from datetime import datetime, date
from core.db import get_connection

LICENSE_SECRET = "WBS_ENTERPRISE_KEY_SALT_2026_MASTER"


def get_machine_id():
    """Returns unique 8-character hardware fingerprint for this machine."""
    raw = ""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                raw, _ = winreg.QueryValueEx(k, "MachineGuid")
        except Exception:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as k:
                    raw, _ = winreg.QueryValueEx(k, "MachineGuid")
            except Exception:
                pass

    if not raw:
        raw = f"{uuid.getnode()}_{os.environ.get('COMPUTERNAME', 'PC')}"

    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8].upper()


def generate_license_sig(plan, expiry_str, machine_id):
    """Generates an 8-char HMAC signature."""
    payload = f"{plan}:{expiry_str}:{machine_id}".upper()
    return hmac.new(LICENSE_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:8].upper()


def generate_commercial_key(plan="Pro", days_valid=365, machine_id="GLOBAL"):
    """
    Generates commercial activation key in format:
    LICENSE-PLAN-YYYYMMDD-MACHID-SIG
    """
    machine_id = str(machine_id).strip().upper() or "GLOBAL"
    plan = str(plan).capitalize()
    exp_date = datetime.now().date()
    from datetime import timedelta
    exp_date += timedelta(days=int(days_valid))
    exp_str = exp_date.strftime("%Y%m%d")
    sig = generate_license_sig(plan, exp_str, machine_id)
    return f"SHAKTIX-{plan.upper()}-{exp_str}-{machine_id}-{sig}"


def validate_key(key_string, target_machine_id=None):
    """
    Validates license key string. Supports both:
    LICENSE-PLAN-YYYYMMDD-MACHID-SIG and WBS-PLAN-YYYYMMDD-MACHID-SIG
    """
    clean = str(key_string or "").strip().upper()
    parts = clean.split("-")
    if len(parts) != 5 or parts[0] not in ("SHAKTIX", "LICENSE", "WBS"):
        return False, None, None, "Invalid format. Expected: LICENSE-PLAN-YYYYMMDD-MACHID-SIG"

    _, plan, exp_str, key_mach, sig = parts

    try:
        exp_date = datetime.strptime(exp_str, "%Y%m%d").date()
    except ValueError:
        return False, None, None, "Invalid expiration date in key."

    # Verify signature
    expected_sig = generate_license_sig(plan, exp_str, key_mach)
    if not hmac.compare_digest(sig, expected_sig):
        return False, None, None, "Invalid cryptographic key signature."

    # Verify machine binding
    curr_mach = target_machine_id or get_machine_id()
    if key_mach != "GLOBAL" and key_mach != curr_mach:
        return False, None, None, f"Key is locked to Machine [{key_mach}], but this device is [{curr_mach}]."

    if exp_date < date.today():
        return False, plan, exp_date, f"License expired on {exp_date.strftime('%Y-%m-%d')}."

    return True, plan, exp_date, None


def get_plan_limits(plan_name):
    """Fetches plan entitlements from SQLite database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, max_contacts, max_campaigns, max_team, allow_api, allow_scheduler FROM plans WHERE LOWER(name) = LOWER(?)", (plan_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)

    # Default fallback limits
    return {
        "name": "Starter",
        "max_contacts": 500,
        "max_campaigns": 10,
        "max_team": 1,
        "allow_api": 0,
        "allow_scheduler": 0
    }


def get_active_license():
    """Checks stored license in SQLite DB and returns status dictionary."""
    curr_mach = get_machine_id()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT license_key, plan, machine_id, expiry_date, status FROM licenses ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()

        if not row:
            return {
                "status": "TRIAL",
                "plan": "Starter (Trial)",
                "machine_id": curr_mach,
                "expiry_date": None,
                "days_remaining": 0,
                "limits": get_plan_limits("Starter"),
                "key": None,
                "label": "Free Trial (500 Contacts / 15 Msgs per Run)"
            }

        key = row["license_key"]
        plan = row["plan"]
        exp_date_str = row["expiry_date"]

        valid, plan_verified, exp_date, err = validate_key(key, curr_mach)
        if not valid:
            return {
                "status": "EXPIRED" if err and "expired" in err.lower() else "INVALID",
                "plan": plan,
                "machine_id": curr_mach,
                "expiry_date": exp_date_str,
                "days_remaining": 0,
                "limits": get_plan_limits("Starter"),
                "key": key,
                "label": f"License Error: {err}"
            }

        days_left = max(0, (exp_date - date.today()).days)
        limits = get_plan_limits(plan_verified)
        return {
            "status": "ACTIVE",
            "plan": plan_verified,
            "machine_id": curr_mach,
            "expiry_date": exp_date.strftime("%Y-%m-%d"),
            "days_remaining": days_left,
            "limits": limits,
            "key": key,
            "label": f"{plan_verified} Active ({days_left} days left)"
        }


def activate_key(key_string):
    """Validates and persists commercial license key."""
    mach = get_machine_id()
    valid, plan, exp_date, err = validate_key(key_string, mach)
    if not valid:
        return False, err

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exp_str = exp_date.strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM licenses")
        cursor.execute("""
            INSERT INTO licenses (license_key, plan, machine_id, expiry_date, status, activated_at)
            VALUES (?, ?, ?, ?, 'ACTIVE', ?)
        """, (key_string.strip().upper(), plan, mach, exp_str, now))
        conn.commit()

    return True, f"Successfully activated {plan} license until {exp_str}."


def deactivate_license():
    """Removes stored license key."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM licenses")
        conn.commit()
    return True, "License deactivated. Switched to Free Trial mode."


def can_dispatch_campaign(recipients_count=1):
    """
    Commercial entitlement gatekeeper before launching campaign dispatches.
    Returns: (allowed: bool, reason_message: str)
    """
    lic = get_active_license()
    stat = lic.get("status")

    if stat in ("EXPIRED", "INVALID"):
        return False, f"Campaign blocked: License is {stat}. {lic.get('label', 'Please renew your commercial license.')}"

    if stat == "TRIAL":
        if recipients_count > 15:
            return False, "Trial mode is limited to 15 recipients per campaign. Upgrade to Pro or Business to remove this limit."

    return True, "Entitlement verified."


# =========================================================================
# Supabase Cloud Licensing & Machine Binding Integration
# =========================================================================
SUPABASE_URL = "https://dcbpqapojfxacpvjobyp.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRjYnBxYXBvamZ4YWNwdmpvYnlwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4MDM4MjAsImV4cCI6MjEwNTM3OTgyMH0.RSt2lJxaPh_JwcpORuBozkUSIYaRrVt1_y9eEPj3YwM"


def check_cloud_license(machine_id=None):
    """
    Checks Supabase Cloud Database for an active license assigned to this machine.
    If found, automatically activates and syncs it locally.
    """
    import json
    import urllib.request
    import urllib.error

    mach = (machine_id or get_machine_id()).upper()
    url = f"{SUPABASE_URL}/rest/v1/licenses?machine_id=eq.{mach}&is_active=eq.true&select=*"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and len(data) > 0:
                lic = data[0]
                key = lic.get("license_key")
                if key:
                    activate_key(key)
                    return True, lic
    except Exception:
        pass
    return False, None
