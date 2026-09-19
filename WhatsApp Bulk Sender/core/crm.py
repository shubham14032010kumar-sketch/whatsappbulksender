"""
Advanced CRM, Groups, Tags & Segmentation Engine (core/crm.py)
Handles contact management, custom fields, group assignments,
tagging, and multi-parameter audience segmentation.
"""

import json
import re
from datetime import datetime
from core.db import get_connection

CONTACT_STATUSES = ["New Lead", "Hot Lead", "Follow-up", "Customer", "VIP"]


# --- CONTACT MANAGEMENT ---
def add_or_update_contact(name, phone, email="", company="", city="", category="", tags="", notes="", status="New Lead", opt_in=1, custom_fields=None, org_id=1):
    """Upserts a single contact record."""
    phone_clean = re.sub(r"[^\d+]", "", str(phone or "").strip())
    if not phone_clean:
        return False, "Valid phone number is mandatory."

    custom_json = json.dumps(custom_fields or {}) if isinstance(custom_fields, dict) else (custom_fields or "{}")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contacts (org_id, name, phone, email, company, city, category, tags, notes, status, opt_in, custom_fields, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(phone) DO UPDATE SET
                name = CASE WHEN excluded.name != '' THEN excluded.name ELSE contacts.name END,
                email = CASE WHEN excluded.email != '' THEN excluded.email ELSE contacts.email END,
                company = CASE WHEN excluded.company != '' THEN excluded.company ELSE contacts.company END,
                city = CASE WHEN excluded.city != '' THEN excluded.city ELSE contacts.city END,
                category = CASE WHEN excluded.category != '' THEN excluded.category ELSE contacts.category END,
                tags = CASE WHEN excluded.tags != '' THEN excluded.tags ELSE contacts.tags END,
                notes = CASE WHEN excluded.notes != '' THEN excluded.notes ELSE contacts.notes END,
                status = excluded.status,
                opt_in = excluded.opt_in,
                custom_fields = excluded.custom_fields,
                updated_at = excluded.updated_at
        """, (org_id, name.strip(), phone_clean, email.strip(), company.strip(), city.strip(), category.strip(), tags.strip(), notes.strip(), status, int(opt_in), custom_json, now, now))
        conn.commit()
        return True, cursor.lastrowid


def bulk_import_contacts(contact_records, org_id=1):
    """
    Bulk inserts/upserts list of contact dicts.
    Returns: (imported_count, error_count)
    """
    imported = 0
    errors = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    rows_to_insert = []
    with get_connection() as conn:
        cursor = conn.cursor()
        for c in contact_records:
            raw_phone = str(c.get("phone", "")).strip()
            phone = re.sub(r"[^\d+]", "", raw_phone)
            if not phone:
                errors += 1
                continue

            name = str(c.get("name", "") or "").strip()
            email = str(c.get("email", "") or "").strip()
            company = str(c.get("company", "") or "").strip()
            city = str(c.get("city", "") or "").strip()
            category = str(c.get("category", "") or "").strip()
            tags = str(c.get("tags", "") or "").strip()
            notes = str(c.get("notes", "") or "").strip()
            status = str(c.get("status", "New Lead") or "New Lead").strip()
            opt_in = int(c.get("opt_in", 1))
            cf = json.dumps(c.get("custom_fields", {})) if isinstance(c.get("custom_fields"), dict) else "{}"

            rows_to_insert.append((
                org_id, name, phone, email, company, city, category, tags, notes, status, opt_in, cf, now, now
            ))

        sql = """
            INSERT INTO contacts (org_id, name, phone, email, company, city, category, tags, notes, status, opt_in, custom_fields, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(phone) DO UPDATE SET
                name = CASE WHEN excluded.name != '' THEN excluded.name ELSE contacts.name END,
                email = CASE WHEN excluded.email != '' THEN excluded.email ELSE contacts.email END,
                company = CASE WHEN excluded.company != '' THEN excluded.company ELSE contacts.company END,
                city = CASE WHEN excluded.city != '' THEN excluded.city ELSE contacts.city END,
                category = CASE WHEN excluded.category != '' THEN excluded.category ELSE contacts.category END,
                tags = CASE WHEN excluded.tags != '' THEN excluded.tags ELSE contacts.tags END,
                notes = CASE WHEN excluded.notes != '' THEN excluded.notes ELSE contacts.notes END,
                status = excluded.status,
                opt_in = excluded.opt_in,
                custom_fields = excluded.custom_fields,
                updated_at = excluded.updated_at
        """
        try:
            cursor.executemany(sql, rows_to_insert)
            conn.commit()
            imported = len(rows_to_insert)
        except Exception:
            # Fallback to single inserts if batch hits a single bad row
            for r in rows_to_insert:
                try:
                    cursor.execute(sql, r)
                    imported += 1
                except Exception:
                    errors += 1
            conn.commit()
    return imported, errors


# --- MULTI-PARAMETER AUDIENCE SEGMENTATION ---
def filter_contacts(city=None, category=None, tag=None, group_id=None, status=None, opt_in=None, search=None, limit=2000, offset=0):
    """
    Powerful multi-parameter segmentation:
    e.g. City = 'Gaya' + Category = 'Hotel' + Tag = 'Website Lead'
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT c.id, c.name, c.phone, c.email, c.company, c.city, c.category, c.tags, c.status, c.opt_in, c.notes, c.last_contacted, c.custom_fields
            FROM contacts c
        """
        joins = []
        where_clauses = ["1=1"]
        params = []

        if group_id and group_id != "All Groups":
            joins.append("JOIN contact_group_members cgm ON c.id = cgm.contact_id")
            where_clauses.append("cgm.group_id = ?")
            params.append(group_id)

        if city and city.strip() and city != "All Cities":
            where_clauses.append("LOWER(c.city) = LOWER(?)")
            params.append(city.strip())

        if category and category.strip() and category != "All Categories":
            where_clauses.append("LOWER(c.category) = LOWER(?)")
            params.append(category.strip())

        if status and status.strip() and status != "All Statuses":
            where_clauses.append("c.status = ?")
            params.append(status.strip())

        if opt_in is not None and opt_in != "All":
            where_clauses.append("c.opt_in = ?")
            params.append(1 if opt_in in (1, "Opted-in", "Yes") else 0)

        if tag and tag.strip() and tag != "All Tags":
            t = tag.strip()
            where_clauses.append("(c.tags LIKE ? OR c.tags LIKE ? OR c.tags = ?)")
            params.extend([f"%,{t},%", f"%{t}%", t])

        if search and search.strip():
            s = f"%{search.strip()}%"
            where_clauses.append("(c.name LIKE ? OR c.phone LIKE ? OR c.company LIKE ? OR c.email LIKE ? OR c.notes LIKE ?)")
            params.extend([s, s, s, s, s])

        full_query = f"{query} {' '.join(joins)} WHERE {' AND '.join(where_clauses)} ORDER BY c.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(full_query, params)
        return [dict(r) for r in cursor.fetchall()]


def get_crm_kpis():
    """Returns key CRM counts and aggregates."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM contacts WHERE opt_in = 1")
        opted_in = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(DISTINCT city) FROM contacts WHERE city != '' AND city IS NOT NULL")
        cities = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(DISTINCT category) FROM contacts WHERE category != '' AND category IS NOT NULL")
        cats = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM contact_groups")
        groups = cursor.fetchone()[0] or 0

        return {
            "total_contacts": total,
            "opted_in": opted_in,
            "total_cities": cities,
            "total_categories": cats,
            "total_groups": groups
        }


# --- GROUPS & TAGS MANAGEMENT ---
def create_group(name, description="", color="#3b82f6"):
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT OR IGNORE INTO contact_groups (name, description, color, created_at) VALUES (?, ?, ?, ?)",
                       (name.strip(), description.strip(), color, now))
        conn.commit()
        return cursor.lastrowid


def get_all_groups():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.id, g.name, g.description, g.color, COUNT(cgm.contact_id) as member_count
            FROM contact_groups g
            LEFT JOIN contact_group_members cgm ON g.id = cgm.group_id
            GROUP BY g.id
            ORDER BY g.name ASC
        """)
        return [dict(r) for r in cursor.fetchall()]


def create_tag(name, color="#10b981"):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO contact_tags (name, color) VALUES (?, ?)", (name.strip(), color))
        conn.commit()
        return cursor.lastrowid


def get_all_tags():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, color FROM contact_tags ORDER BY name ASC")
        return [dict(r) for r in cursor.fetchall()]


def get_unique_values(field_name):
    allowed = {"city", "category", "status"}
    if field_name not in allowed:
        return []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT DISTINCT {field_name} FROM contacts WHERE {field_name} != '' AND {field_name} IS NOT NULL ORDER BY {field_name} ASC")
        return [r[0] for r in cursor.fetchall()]


def delete_contacts(contact_ids):
    if not contact_ids:
        return 0
    with get_connection() as conn:
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(contact_ids))
        cursor.execute(f"DELETE FROM contacts WHERE id IN ({placeholders})", contact_ids)
        deleted = cursor.rowcount
        conn.commit()
        return deleted
