"""
Enterprise Database Manager (core/db.py)
Unified SQLite database layer implementing all 19 Master Enterprise tables,
indexing, migrations, and thread-safe operations.
"""

import sqlite3
import os
import json
from datetime import datetime

DB_FILE = os.path.join(os.getcwd(), "app_data.db")


def get_connection():
    """Returns a SQLite connection with foreign key support enabled."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Creates all 19 Enterprise tables and pre-seeds default plans and settings."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Users Table (Authentication & RBAC)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'Owner', -- Owner, Admin, Manager, Staff
                status TEXT DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, SUSPENDED
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # 2. Organizations Table (Multi-tenant)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                owner_id INTEGER,
                plan_id INTEGER DEFAULT 2,
                created_at TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)

        # 3. Team Members Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                permissions TEXT, -- JSON array of permissions
                joined_at TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 4. Contacts Table (Advanced CRM)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER DEFAULT 1,
                name TEXT,
                phone TEXT UNIQUE NOT NULL,
                email TEXT,
                company TEXT,
                city TEXT,
                category TEXT,
                tags TEXT,
                notes TEXT,
                status TEXT DEFAULT 'New Lead', -- New Lead, Hot Lead, Follow-up, Customer, VIP
                opt_in INTEGER DEFAULT 1, -- 1=Opted-in, 0=Opted-out
                last_contacted TEXT,
                custom_fields TEXT, -- JSON key-value store
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Auto-migrate contacts table if existing schema was from older version
        cursor.execute("PRAGMA table_info(contacts)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        contacts_cols = {
            "org_id": "INTEGER DEFAULT 1",
            "name": "TEXT",
            "email": "TEXT",
            "company": "TEXT",
            "city": "TEXT",
            "category": "TEXT",
            "tags": "TEXT",
            "notes": "TEXT",
            "status": "TEXT DEFAULT 'New Lead'",
            "opt_in": "INTEGER DEFAULT 1",
            "last_contacted": "TEXT",
            "custom_fields": "TEXT",
            "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TEXT DEFAULT CURRENT_TIMESTAMP"
        }
        for col, col_type in contacts_cols.items():
            if col not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE contacts ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_city ON contacts(city)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contacts_category ON contacts(category)")

        # 5. Contact Groups Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER DEFAULT 1,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#3b82f6',
                created_at TEXT NOT NULL
            )
        """)

        # 6. Contact Tags Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER DEFAULT 1,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#10b981'
            )
        """)

        # 7. Contact Group Members (Many-to-Many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_group_members (
                contact_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                PRIMARY KEY (contact_id, group_id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES contact_groups(id) ON DELETE CASCADE
            )
        """)

        # 8. Templates Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER DEFAULT 1,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                has_media INTEGER DEFAULT 0,
                media_path TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # 9. Campaigns Workspace Table (State Machine)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER DEFAULT 1,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'Draft', -- Draft, Scheduled, Running, Paused, Completed, Failed
                template_id INTEGER,
                scheduled_at TEXT,
                min_delay INTEGER DEFAULT 8,
                max_delay INTEGER DEFAULT 15,
                total_recipients INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE SET NULL
            )
        """)

        # 10. Campaign Recipients Audit Details
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                contact_id INTEGER,
                phone TEXT NOT NULL,
                name TEXT,
                status TEXT NOT NULL, -- PENDING, SENT, FAILED, SKIPPED
                sent_at TEXT,
                error_message TEXT,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_recipients_campaign ON campaign_recipients(campaign_id)")

        # 11. Scheduled Campaigns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER UNIQUE NOT NULL,
                trigger_time TEXT NOT NULL,
                repeat_rule TEXT DEFAULT 'ONCE', -- ONCE, DAILY, WEEKLY
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            )
        """)

        # 12. Campaign Reports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER UNIQUE NOT NULL,
                total_target INTEGER NOT NULL,
                delivered INTEGER NOT NULL,
                failed INTEGER NOT NULL,
                response_rate REAL DEFAULT 0.0,
                opt_outs INTEGER DEFAULT 0,
                exported_at TEXT NOT NULL,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            )
        """)

        # 13. Subscriptions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                status TEXT DEFAULT 'ACTIVE', -- ACTIVE, EXPIRED, CANCELLED
                start_date TEXT NOT NULL,
                renew_date TEXT NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
        """)

        # 14. Plans & Entitlements Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL, -- Starter, Pro, Business
                max_contacts INTEGER NOT NULL,
                max_campaigns INTEGER NOT NULL,
                max_team INTEGER NOT NULL,
                allow_api INTEGER DEFAULT 0,
                allow_scheduler INTEGER DEFAULT 1,
                price_inr INTEGER DEFAULT 0
            )
        """)

        # 15. Licenses Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_key TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                plan TEXT NOT NULL,
                machine_id TEXT NOT NULL,
                device_limit INTEGER DEFAULT 1,
                expiry_date TEXT NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                activated_at TEXT NOT NULL
            )
        """)

        # 16. Monthly Usage Metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER DEFAULT 1,
                month_year TEXT NOT NULL, -- e.g. '2026-09'
                messages_sent INTEGER DEFAULT 0,
                campaigns_run INTEGER DEFAULT 0,
                UNIQUE(org_id, month_year)
            )
        """)

        # 17. REST API Keys
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER DEFAULT 1,
                key_hash TEXT UNIQUE NOT NULL,
                key_prefix TEXT NOT NULL,
                label TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)

        # 18. Audit Logs (Who / What / When)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                org_id INTEGER DEFAULT 1,
                user_name TEXT NOT NULL,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                details TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC)")

        # 19. Enterprise Key-Value Settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                updated_at TEXT NOT NULL
            )
        """)

        # Backward compatibility tables (templates, blacklist, campaign_history)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                reason TEXT,
                added_at TEXT NOT NULL
            )
        """)
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER,
                phone TEXT NOT NULL,
                name TEXT,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                error_msg TEXT
            )
        """)

        conn.commit()

        # Seed default plans if not present
        cursor.execute("SELECT COUNT(*) FROM plans")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO plans (name, max_contacts, max_campaigns, max_team, allow_api, allow_scheduler, price_inr)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                ("Starter", 500, 10, 1, 0, 0, 499),
                ("Pro", 100000, 9999, 3, 1, 1, 1999),
                ("Business", 9999999, 99999, 10, 1, 1, 4999)
            ])
            conn.commit()

        # Seed default organization if not present
        cursor.execute("SELECT COUNT(*) FROM organizations")
        if cursor.fetchone()[0] == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO organizations (name, created_at) VALUES ('Enterprise Workspace', ?)", (now,))
            conn.commit()

        # Seed default groups if not present
        cursor.execute("SELECT COUNT(*) FROM contact_groups")
        if cursor.fetchone()[0] == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.executemany("""
                INSERT INTO contact_groups (name, description, color, created_at)
                VALUES (?, ?, ?, ?)
            """, [
                ("Hotels & Hospitality", "Hotels, Resorts, Lodges", "#3b82f6", now),
                ("Doctors & Healthcare", "Clinics, Hospitals, Doctors", "#10b981", now),
                ("Restaurants & Cafes", "Food & Dining businesses", "#f59e0b", now),
                ("Schools & Institutes", "Coaching, Schools, Colleges", "#8b5cf6", now),
                ("Real Estate", "Brokers, Developers, Builders", "#ec4899", now)
            ])
            conn.commit()

        # Seed default tags if not present
        cursor.execute("SELECT COUNT(*) FROM contact_tags")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO contact_tags (name, color)
                VALUES (?, ?)
            """, [
                ("Hot Lead", "#ef4444"),
                ("New Lead", "#3b82f6"),
                ("Follow-up", "#f59e0b"),
                ("Customer", "#10b981"),
                ("VIP", "#8b5cf6"),
                ("Website Lead", "#06b6d4")
            ])
            conn.commit()

        # Seed default settings if not present
        cursor.execute("SELECT COUNT(*) FROM settings")
        if cursor.fetchone()[0] == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            default_settings = [
                ("company_name", "Enterprise Bulk Sender", "general"),
                ("country_code_default", "91", "campaign"),
                ("min_delay_default", "8", "campaign"),
                ("max_delay_default", "15", "campaign"),
                ("batch_rest_mins", "3", "safety"),
                ("batch_rest_count", "30", "safety"),
                ("typing_simulation", "1", "safety"),
                ("auto_backup_daily", "1", "storage"),
                ("api_server_enabled", "1", "api"),
                ("api_server_port", "8000", "api")
            ]
            cursor.executemany("INSERT OR REPLACE INTO settings (key, value, category, updated_at) VALUES (?, ?, ?, ?)",
                               [(k, v, c, now) for k, v, c in default_settings])
            conn.commit()


# Initialize database schema on load
init_database()
init_db = init_database
