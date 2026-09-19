"""
Database Backup & Restore Manager (core/backup.py)
Supports manual and automated timestamped SQLite snapshots and 1-click restore.
"""

import os
import shutil
import zipfile
from datetime import datetime
from core.db import DB_FILE

BACKUP_DIR = os.path.join(os.getcwd(), "backups")


def create_backup(dest_folder=None):
    """Creates a compressed timestamped ZIP backup of the application database."""
    target_dir = dest_folder or BACKUP_DIR
    os.makedirs(target_dir, exist_ok=True)

    if not os.path.exists(DB_FILE):
        return False, "Database file does not exist yet."

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"wbs_database_backup_{ts}.zip"
    zip_path = os.path.join(target_dir, zip_name)

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_FILE, arcname="app_data.db")
        return True, zip_path
    except Exception as e:
        return False, str(e)


def list_backups(dest_folder=None):
    """Lists existing backup ZIP files."""
    target_dir = dest_folder or BACKUP_DIR
    if not os.path.exists(target_dir):
        return []
    files = []
    for f in os.listdir(target_dir):
        if f.endswith(".zip") and "backup" in f:
            full = os.path.join(target_dir, f)
            files.append({
                "filename": f,
                "path": full,
                "size_kb": round(os.path.getsize(full) / 1024, 1),
                "date": datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M:%S")
            })
    files.sort(key=lambda x: x["date"], reverse=True)
    return files


def restore_backup(backup_zip_path):
    """Restores database from a given ZIP archive after taking a safety backup."""
    if not os.path.exists(backup_zip_path):
        return False, "Backup file not found."

    try:
        # Create safety snapshot of current DB
        if os.path.exists(DB_FILE):
            shutil.copyfile(DB_FILE, DB_FILE + ".safety_copy")

        with zipfile.ZipFile(backup_zip_path, 'r') as zf:
            zf.extract("app_data.db", path=os.path.dirname(DB_FILE))
        return True, "Database restored successfully."
    except Exception as e:
        return False, f"Restore failed: {str(e)}"
