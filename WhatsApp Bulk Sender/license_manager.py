"""
License & Anti-Piracy Manager for WhatsApp Bulk Campaign Sender
Provides hardware fingerprinting, HMAC-SHA256 license signature verification,
and tier limits (TRIAL, PRO, BUSINESS).
"""

import os
import sys
import hmac
import hashlib
import uuid
import subprocess
from datetime import datetime, date

import db_manager

# Private secret salt for HMAC signature verification (Keep secure in production)
LICENSE_SECRET_SALT = "WBS_ENTERPRISE_SECRET_SALT_2026_MASTER_SIG"

PLAN_LIMITS = {
    "TRIAL": {
        "max_messages_per_campaign": 15,
        "allow_crm_export": False,
        "allow_scheduled_send": False,
        "label": "Free Trial (15 Msgs Limit)"
    },
    "PRO": {
        "max_messages_per_campaign": 9999999,
        "allow_crm_export": True,
        "allow_scheduled_send": True,
        "label": "PRO License (Unlimited)"
    },
    "BUSINESS": {
        "max_messages_per_campaign": 9999999,
        "allow_crm_export": True,
        "allow_scheduled_send": True,
        "label": "Business Enterprise"
    }
}


def get_machine_fingerprint():
    """
    Extracts a hardware-tied unique identifier for Windows (MachineGuid / ComputerName / UUID).
    Returns a clean 8-character uppercase hex string instantly without subprocess calls.
    """
    raw_id = ""
    if sys.platform == "win32":
        try:
            import winreg
            # Access 64-bit registry view for MachineGuid
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                raw_id, _ = winreg.QueryValueEx(key, "MachineGuid")
        except Exception:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as key:
                    raw_id, _ = winreg.QueryValueEx(key, "MachineGuid")
            except Exception:
                pass

    if not raw_id:
        computer = os.environ.get("COMPUTERNAME", "PC")
        user = os.environ.get("USERNAME", "USER")
        raw_id = f"{uuid.getnode()}_{computer}_{user}"

    # Create short 8-char hardware hash
    h = hashlib.sha256(raw_id.encode("utf-8")).hexdigest().upper()
    return h[:8]


def generate_license_signature(plan, expiry_str, machine_id):
    """Generates an 8-char HMAC signature for given license components."""
    data = f"{plan}:{expiry_str}:{machine_id}".upper()
    sig = hmac.new(LICENSE_SECRET_SALT.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest().upper()
    return sig[:8]


def parse_and_validate_key(key_string, expected_machine_id=None):
    """
    Validates license key format: WBS-<PLAN>-<YYYYMMDD>-<MACHINE_ID>-<SIGNATURE>
    Or Wildcard: WBS-<PLAN>-<YYYYMMDD>-GLOBAL-<SIGNATURE>
    Returns: (is_valid, plan, expiry_date, error_message)
    """
    clean_key = str(key_string or "").strip().upper()
    parts = clean_key.split("-")
    if len(parts) != 5 or parts[0] != "WBS":
        return False, None, None, "Invalid license key format. Expected: WBS-PLAN-YYYYMMDD-MACHID-SIG"

    _, plan, expiry_str, key_machine_id, sig = parts

    if plan not in PLAN_LIMITS:
        return False, None, None, f"Unknown plan '{plan}'"

    # Check Date Format
    try:
        exp_date = datetime.strptime(expiry_str, "%Y%m%d").date()
    except ValueError:
        return False, None, None, "Invalid expiry date in key."

    # Verify signature
    expected_sig = generate_license_signature(plan, expiry_str, key_machine_id)
    if not hmac.compare_digest(sig, expected_sig):
        return False, None, None, "Invalid cryptographic key signature. Key was modified or forged."

    # Verify Machine ID match (unless wildcard GLOBAL)
    curr_machine = expected_machine_id or get_machine_fingerprint()
    if key_machine_id != "GLOBAL" and key_machine_id != curr_machine:
        return False, None, None, f"License key is locked to Machine [{key_machine_id}], but this device is [{curr_machine}]."

    # Verify Expiration
    today = date.today()
    if exp_date < today:
        return False, plan, exp_date, f"License key expired on {exp_date.strftime('%Y-%m-%d')}."

    return True, plan, exp_date, None


def get_current_license_status():
    """
    Checks stored license in SQLite DB and returns status dictionary.
    Returns:
    {
        'status': 'ACTIVE' | 'TRIAL' | 'EXPIRED' | 'INVALID',
        'plan': 'TRIAL' | 'PRO' | 'BUSINESS',
        'machine_id': '...',
        'expiry_date': 'YYYY-MM-DD' or None,
        'days_remaining': int,
        'limits': dict,
        'key': '...' or None,
        'message': '...'
    }
    """
    curr_machine = get_machine_fingerprint()
    saved = db_manager.get_saved_license()

    if not saved:
        return {
            "status": "TRIAL",
            "plan": "TRIAL",
            "machine_id": curr_machine,
            "expiry_date": None,
            "days_remaining": 0,
            "limits": PLAN_LIMITS["TRIAL"],
            "key": None,
            "message": "Running on Free Trial mode."
        }

    key, plan, machine_id, expiry_date_str, status, activated_at = saved
    is_valid, plan_verified, exp_date, err = parse_and_validate_key(key, curr_machine)

    if not is_valid:
        if err and "expired" in err.lower():
            return {
                "status": "EXPIRED",
                "plan": plan,
                "machine_id": curr_machine,
                "expiry_date": expiry_date_str,
                "days_remaining": 0,
                "limits": PLAN_LIMITS["TRIAL"],
                "key": key,
                "message": f"License expired! ({err})"
            }
        return {
            "status": "INVALID",
            "plan": "TRIAL",
            "machine_id": curr_machine,
            "expiry_date": expiry_date_str,
            "days_remaining": 0,
            "limits": PLAN_LIMITS["TRIAL"],
            "key": key,
            "message": f"License check failed: {err}"
        }

    today = date.today()
    days_left = (exp_date - today).days

    return {
        "status": "ACTIVE",
        "plan": plan_verified,
        "machine_id": curr_machine,
        "expiry_date": exp_date.strftime("%Y-%m-%d"),
        "days_remaining": max(0, days_left),
        "limits": PLAN_LIMITS.get(plan_verified, PLAN_LIMITS["PRO"]),
        "key": key,
        "message": f"{plan_verified} Active ({days_left} days left)"
    }


def activate_license_key(key_string):
    """
    Validates and stores the key into the database.
    Returns: (success: bool, message: str)
    """
    machine_id = get_machine_fingerprint()
    is_valid, plan, exp_date, err = parse_and_validate_key(key_string, machine_id)
    if not is_valid:
        return False, err

    expiry_str = exp_date.strftime("%Y-%m-%d")
    db_manager.save_license_record(key_string.strip().upper(), plan, machine_id, expiry_str)
    return True, f"Successfully activated {plan} license! Valid until {expiry_str}."


def deactivate_current_license():
    """Removes stored license key."""
    db_manager.remove_saved_license()
    return True, "License key removed. Reverted to Free Trial."
