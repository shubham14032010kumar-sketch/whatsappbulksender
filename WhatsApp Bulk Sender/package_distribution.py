"""
Distribution Packager for Enterprise WhatsApp Bulk Campaign Sender
Generates release archives excluding virtual environments, caches, and logs.
"""
import os
import zipfile

SOURCE_DIR = r"C:\Users\DELL\Desktop\WhatsApp Bulk Sender\WhatsApp Bulk Sender"
OUTPUT_ZIP_V1 = r"C:\Users\DELL\Desktop\WhatsApp Bulk Sender\WhatsApp_Bulk_Sender_V1_Commercial.zip"
OUTPUT_ZIP_V2 = r"C:\Users\DELL\Desktop\WhatsApp Bulk Sender\WhatsApp_Bulk_Sender_V2_AI_Enterprise.zip"

EXCLUDE_DIRS = {".venv", "__pycache__", "whatsapp_chrome_profile", "backups", ".git", ".idea", ".vscode"}
EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd"}

def package_to(target_zip):
    if os.path.exists(target_zip):
        try:
            os.remove(target_zip)
        except Exception:
            pass

    file_count = 0
    with zipfile.ZipFile(target_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(SOURCE_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUDE_EXTS:
                    continue
                
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.dirname(SOURCE_DIR))
                zf.write(full_path, arcname=rel_path)
                file_count += 1

    size_kb = os.path.getsize(target_zip) / 1024
    print(f"Packaged {file_count} files into {os.path.basename(target_zip)} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    package_to(OUTPUT_ZIP_V1)
    package_to(OUTPUT_ZIP_V2)
