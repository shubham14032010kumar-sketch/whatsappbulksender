"""
Client Edition Release Packager (package_client_edition.py)
Creates an end-user client distribution package ready for sale.
Excludes Super Admin licensing tools, test suites, and internal files.
Sets client_mode.flag so Super Admin tab is strictly hidden.
"""

import os
import zipfile
import shutil

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SOURCE_DIR)
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
OUTPUT_ZIP = os.path.join(DIST_DIR, "WhatsApp_Bulk_Sender_Client_Edition.zip")

EXCLUDE_DIRS = {
    ".venv",
    "__pycache__",
    "whatsapp_chrome_profile",
    "backups",
    ".git",
    ".idea",
    ".vscode",
    "dist"
}

EXCLUDE_FILES = {
    "license_generator.py",
    "generate_license.bat",
    "Generate_License_Key.bat",
    "package_distribution.py",
    "package_client_edition.py",
    "build_exe.bat",
    "export_patna_leads.py"
}

EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd", ".log"}


def build_client_package():
    os.makedirs(DIST_DIR, exist_ok=True)
    if os.path.exists(OUTPUT_ZIP):
        try:
            os.remove(OUTPUT_ZIP)
        except Exception:
            pass

    # Ensure client_mode.flag is temporarily placed for packaging
    flag_path = os.path.join(SOURCE_DIR, "client_mode.flag")
    flag_created_by_us = False
    if not os.path.exists(flag_path):
        with open(flag_path, "w", encoding="utf-8") as f:
            f.write("CLIENT_EDITION=1\nSUPER_ADMIN_LOCKED=1\n")
        flag_created_by_us = True

    packed_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(SOURCE_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            for file in files:
                fname = file.lower()
                ext = os.path.splitext(file)[1].lower()

                if ext in EXCLUDE_EXTS:
                    continue
                if file in EXCLUDE_FILES:
                    continue
                if fname.startswith("test_"):
                    continue
                if fname.startswith("audioengine_") or fname.startswith("scenesdata_"):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, SOURCE_DIR)
                # Nest under clean folder inside zip
                arc_name = os.path.join("WhatsApp Bulk Sender Client Edition", rel_path)
                zf.write(full_path, arcname=arc_name)
                packed_count += 1

        # Also add easy desktop launcher at root of zip
        launcher_content = """@echo off
title Launch WhatsApp Bulk Campaign Sender
cd /d "%~dp0WhatsApp Bulk Sender Client Edition"
call run_app.bat %*
"""
        zf.writestr("Double_Click_To_Launch.bat", launcher_content)

    # Clean up local flag so owner remains in owner mode
    if flag_created_by_us and os.path.exists(flag_path):
        os.remove(flag_path)

    size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print("=" * 65)
    print(f"CLIENT COMMERCIAL PACKAGE CREATED SUCCESSFULLY!")
    print(f"File: {OUTPUT_ZIP}")
    print(f"Total Files: {packed_count} | Size: {size_mb:.2f} MB")
    print(f"Notice: Super Admin tools & generator scripts excluded.")
    print("=" * 65)
    return OUTPUT_ZIP


if __name__ == "__main__":
    build_client_package()
