"""
Authentication & Team RBAC System (core/auth.py)
Provides secure password hashing (PBKDF2-HMAC-SHA256), session state,
user registration, login verification, and Role-Based Access Control.
"""

import os
import hashlib
import hmac
import secrets
from datetime import datetime
from core.db import get_connection

ROLES_PERMISSIONS = {
    "Owner": {"all", "users", "campaigns", "crm", "reports", "settings", "license", "api"},
    "Admin": {"users", "campaigns", "crm", "reports", "settings"},
    "Manager": {"campaigns", "reports", "crm"},
    "Staff": {"contacts", "campaigns"}
}


def hash_password(password, salt=None):
    """Generates a secure PBKDF2 hash with 100,000 iterations and 16-byte salt."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"


def verify_password(stored_hash, password_attempt):
    """Verifies candidate password against stored hash using constant-time comparison."""
    try:
        salt, key_hex = stored_hash.split('$')
        candidate_key = hashlib.pbkdf2_hmac(
            'sha256',
            password_attempt.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hmac.compare_digest(candidate_key.hex(), key_hex)
    except Exception:
        return False


def register_user(name, email, password, role="Staff"):
    """Creates a new user with hashed credentials."""
    email_clean = email.strip().lower()
    if not email_clean or not password or not name:
        return False, "Name, email, and password are required."

    if role not in ROLES_PERMISSIONS:
        role = "Staff"

    pwd_hash = hash_password(password)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, role, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'ACTIVE', ?, ?)
            """, (name.strip(), email_clean, pwd_hash, role, now, now))
            user_id = cursor.lastrowid
            conn.commit()
            return True, {"id": user_id, "name": name, "email": email_clean, "role": role}
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "A user with this email address already exists."
        return False, f"Registration failed: {str(e)}"


def authenticate_user(email, password):
    """Authenticates email and password. Returns user dict on success, None on failure."""
    email_clean = email.strip().lower()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, password_hash, role, status FROM users WHERE LOWER(email) = ?", (email_clean,))
        row = cursor.fetchone()
        if not row:
            return None, "Invalid email or password."

        if row["status"] != "ACTIVE":
            return None, "Account is disabled. Contact your administrator."

        if verify_password(row["password_hash"], password):
            user_info = {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "role": row["role"]
            }
            return user_info, "Login successful."
        return None, "Invalid email or password."


def change_password(user_id, old_password, new_password):
    """Changes user password after validating current password."""
    if len(new_password) < 4:
        return False, "New password must be at least 4 characters long."

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "User not found."

        if not verify_password(row["password_hash"], old_password):
            return False, "Current password is incorrect."

        new_hash = hash_password(new_password)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?", (new_hash, now, user_id))
        conn.commit()
        return True, "Password updated successfully."


def get_all_users():
    """Returns list of all users for Admin panel."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role, status, created_at FROM users ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]


def delete_user(user_id):
    """Deletes user by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


class SessionManager:
    """Manages local active user session in application memory."""
    _current_user = None

    @classmethod
    def set_user(cls, user_dict):
        cls._current_user = user_dict

    @classmethod
    def get_user(cls):
        return cls._current_user

    @classmethod
    def is_authenticated(cls):
        return cls._current_user is not None

    @classmethod
    def has_permission(cls, perm):
        if not cls._current_user:
            return False
        role = cls._current_user.get("role", "Staff")
        perms = ROLES_PERMISSIONS.get(role, set())
        return "all" in perms or perm in perms

    @classmethod
    def logout(cls):
        cls._current_user = None


# Ensure at least one default Owner user exists
def ensure_default_owner():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            register_user("System Owner", "admin@enterprise.local", "admin123", role="Owner")


ensure_default_owner()
