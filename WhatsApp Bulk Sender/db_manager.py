"""
Database Manager for WhatsApp Bulk Campaign Sender
Handles local SQLite storage for templates, blacklist, and campaign execution history.
"""

import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.getcwd(), "app_data.db")


def get_connection():
    return sqlite3.connect(DB_FILE, timeout=30.0)


def init_db():
    """Initializes tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Message Templates Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # 2. Blacklist Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                reason TEXT,
                added_at TEXT NOT NULL
            )
        """)

        # 3. Campaign History Summary Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_name TEXT NOT NULL,
                total_contacts INTEGER NOT NULL,
                sent_count INTEGER NOT NULL,
                failed_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # 4. Campaign Details Audit Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER,
                phone TEXT NOT NULL,
                name TEXT,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                error_msg TEXT,
                FOREIGN KEY (campaign_id) REFERENCES campaign_history (id)
            )
        """)

        # 5. Advanced CRM Contacts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT UNIQUE NOT NULL,
                company TEXT,
                city TEXT,
                category TEXT,
                tags TEXT,
                opt_in INTEGER DEFAULT 1,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 6. Commercial License Storage Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS license_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT UNIQUE NOT NULL,
                plan TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                activated_at TEXT NOT NULL
            )
        """)

        conn.commit()


# --- TEMPLATE FUNCTIONS ---
def save_template(title, content):
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO templates (title, content, created_at) VALUES (?, ?, ?)", (title, content, now))
        conn.commit()


def get_all_templates():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, content, created_at FROM templates ORDER BY id DESC")
        return cursor.fetchall()


def delete_template(template_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
        conn.commit()


# --- BLACKLIST FUNCTIONS ---
def add_to_blacklist(phone, reason="Unsubscribed"):
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT OR REPLACE INTO blacklist (phone, reason, added_at) VALUES (?, ?, ?)", (phone, reason, now))
        conn.commit()


def get_blacklist():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, phone, reason, added_at FROM blacklist ORDER BY id DESC")
        return cursor.fetchall()


def remove_from_blacklist(blacklist_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM blacklist WHERE id = ?", (blacklist_id,))
        conn.commit()


def get_blacklisted_numbers_set():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM blacklist")
        rows = cursor.fetchall()
        return {r[0] for r in rows}


# --- CAMPAIGN HISTORY FUNCTIONS ---
def create_campaign_record(name, total_contacts):
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO campaign_history (campaign_name, total_contacts, sent_count, failed_count, created_at) VALUES (?, ?, 0, 0, ?)", (name, total_contacts, now))
        conn.commit()
        return cursor.lastrowid


def update_campaign_summary(campaign_id, sent_count, failed_count):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE campaign_history SET sent_count = ?, failed_count = ? WHERE id = ?", (sent_count, failed_count, campaign_id))
        conn.commit()


def log_campaign_detail(campaign_id, phone, name, status, error_msg=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO campaign_details (campaign_id, phone, name, status, timestamp, error_msg) VALUES (?, ?, ?, ?, ?, ?)",
            (campaign_id, phone, name, status, now, error_msg)
        )
        conn.commit()


def get_all_campaigns():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, campaign_name, total_contacts, sent_count, failed_count, created_at FROM campaign_history ORDER BY id DESC")
        return cursor.fetchall()


def get_campaign_details(campaign_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT phone, name, status, timestamp, error_msg FROM campaign_details WHERE campaign_id = ?", (campaign_id,))
        return cursor.fetchall()


# --- ADVANCED CRM CONTACTS FUNCTIONS ---
def add_or_update_contact(name, phone, company="", city="", category="", tags="", notes="", opt_in=1):
    """Adds a new contact or updates existing contact matched by phone number."""
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO contacts (name, phone, company, city, category, tags, notes, opt_in, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(phone) DO UPDATE SET
                name = excluded.name,
                company = excluded.company,
                city = excluded.city,
                category = excluded.category,
                tags = excluded.tags,
                notes = excluded.notes,
                opt_in = excluded.opt_in,
                updated_at = excluded.updated_at
        """, (name, phone, company, city, category, tags, notes, opt_in, now, now))
        conn.commit()
        return cursor.lastrowid


def bulk_import_contacts(contact_records):
    """
    Imports a list of contact dicts/tuples into CRM with upsert.
    Each item in contact_records should have:
    {'name': ..., 'phone': ..., 'company': ..., 'city': ..., 'category': ..., 'tags': ..., 'notes': ...}
    Returns: (imported_count, error_count)
    """
    imported = 0
    errors = 0
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for c in contact_records:
            try:
                phone = str(c.get("phone", "")).strip()
                if not phone:
                    errors += 1
                    continue
                name = c.get("name", "") or ""
                company = c.get("company", "") or ""
                city = c.get("city", "") or ""
                category = c.get("category", "") or ""
                tags = c.get("tags", "") or ""
                notes = c.get("notes", "") or ""
                opt_in = int(c.get("opt_in", 1))

                cursor.execute("""
                    INSERT INTO contacts (name, phone, company, city, category, tags, notes, opt_in, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(phone) DO UPDATE SET
                        name = CASE WHEN excluded.name != '' THEN excluded.name ELSE contacts.name END,
                        company = CASE WHEN excluded.company != '' THEN excluded.company ELSE contacts.company END,
                        city = CASE WHEN excluded.city != '' THEN excluded.city ELSE contacts.city END,
                        category = CASE WHEN excluded.category != '' THEN excluded.category ELSE contacts.category END,
                        tags = CASE WHEN excluded.tags != '' THEN excluded.tags ELSE contacts.tags END,
                        notes = CASE WHEN excluded.notes != '' THEN excluded.notes ELSE contacts.notes END,
                        updated_at = excluded.updated_at
                """, (name, phone, company, city, category, tags, notes, opt_in, now, now))
                imported += 1
            except Exception:
                errors += 1
        conn.commit()
    return imported, errors


def get_filtered_contacts(city=None, category=None, tag=None, search=None, limit=2000, offset=0):
    """Returns contacts matching the given filters."""
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT id, name, phone, company, city, category, tags, opt_in, notes, updated_at FROM contacts WHERE 1=1"
        params = []

        if city and city.strip() and city != "All Cities":
            query += " AND LOWER(city) = LOWER(?)"
            params.append(city.strip())

        if category and category.strip() and category != "All Categories":
            query += " AND LOWER(category) = LOWER(?)"
            params.append(category.strip())

        if tag and tag.strip() and tag != "All Tags":
            query += " AND (tags LIKE ? OR tags LIKE ? OR tags = ?)"
            tag_val = tag.strip()
            params.extend([f"%,{tag_val},%", f"%{tag_val}%", tag_val])

        if search and search.strip():
            term = f"%{search.strip()}%"
            query += " AND (name LIKE ? OR phone LIKE ? OR company LIKE ? OR notes LIKE ?)"
            params.extend([term, term, term, term])

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        return cursor.fetchall()


def get_crm_stats():
    """Returns aggregate counts for contacts, cities, and categories."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total_contacts = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(DISTINCT city) FROM contacts WHERE city != '' AND city IS NOT NULL")
        total_cities = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(DISTINCT category) FROM contacts WHERE category != '' AND category IS NOT NULL")
        total_categories = cursor.fetchone()[0] or 0

        return {
            "total_contacts": total_contacts,
            "total_cities": total_cities,
            "total_categories": total_categories
        }


def get_unique_crm_values(column_name):
    """Returns unique non-empty sorted values for dropdown filters (city, category, etc.)."""
    allowed_columns = {"city", "category", "tags"}
    if column_name not in allowed_columns:
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        if column_name == "tags":
            cursor.execute("SELECT tags FROM contacts WHERE tags != '' AND tags IS NOT NULL")
            raw_tags = cursor.fetchall()
            unique_tags = set()
            for r in raw_tags:
                if r[0]:
                    parts = [p.strip() for p in str(r[0]).split(",") if p.strip()]
                    unique_tags.update(parts)
            return sorted(list(unique_tags))
        else:
            cursor.execute(f"SELECT DISTINCT {column_name} FROM contacts WHERE {column_name} != '' AND {column_name} IS NOT NULL ORDER BY {column_name} ASC")
            return [r[0] for r in cursor.fetchall() if r[0]]


def delete_contacts_by_ids(contact_ids):
    """Deletes list of contact IDs from database."""
    if not contact_ids:
        return 0
    with get_connection() as conn:
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(contact_ids))
        cursor.execute(f"DELETE FROM contacts WHERE id IN ({placeholders})", contact_ids)
        deleted = cursor.rowcount
        conn.commit()
        return deleted


# --- COMMERCIAL LICENSE STORAGE FUNCTIONS ---
def save_license_record(license_key, plan, machine_id, expiry_date):
    """Saves or updates active license record in local DB."""
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("DELETE FROM license_keys")  # keep only active key
        cursor.execute("""
            INSERT INTO license_keys (license_key, plan, machine_id, expiry_date, status, activated_at)
            VALUES (?, ?, ?, ?, 'ACTIVE', ?)
        """, (license_key, plan, machine_id, expiry_date, now))
        conn.commit()


def get_saved_license():
    """Retrieves current stored license record if any."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT license_key, plan, machine_id, expiry_date, status, activated_at FROM license_keys ORDER BY id DESC LIMIT 1")
        return cursor.fetchone()


def remove_saved_license():
    """Removes stored license key."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM license_keys")
        conn.commit()


# Initialize database schema on load
init_db()
