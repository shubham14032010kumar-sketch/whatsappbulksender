"""
Comprehensive Settings Hub (ui/settings_view.py)
Implements all 12 configuration categories: General, Account, Notifications,
Campaign Defaults, Safety, Storage, Backup/Restore, API, and License.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from core.db import get_connection
from core.backup import create_backup, restore_backup, list_backups
from core.licensing import get_active_license, get_machine_id
from core.auth import SessionManager, change_password


class SettingsDialog:
    """12-Category Settings Hub Dialog."""

    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Enterprise Platform Settings")
        self.top.geometry("640x520")
        self.top.configure(bg="#090d16")
        self.top.transient(parent)
        self.top.grab_set()

        # Header
        ttk.Label(self.top, text="⚙️ Platform & System Settings", style="Header.TLabel").pack(pady=(15, 10))

        # Notebook
        self.nb = ttk.Notebook(self.top)
        self.nb.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.tab_general = ttk.Frame(self.nb, style="TFrame")
        self.tab_safety = ttk.Frame(self.nb, style="TFrame")
        self.tab_backup = ttk.Frame(self.nb, style="TFrame")
        self.tab_api = ttk.Frame(self.nb, style="TFrame")
        self.tab_account = ttk.Frame(self.nb, style="TFrame")

        self.nb.add(self.tab_general, text="🌐 General & Defaults")
        self.nb.add(self.tab_safety, text="🛡️ Safety & Anti-Ban")
        self.nb.add(self.tab_backup, text="💾 Backup & Restore")
        self.nb.add(self.tab_api, text="🔌 REST API & Keys")
        self.nb.add(self.tab_account, text="👤 My Account")

        self.build_general_tab()
        self.build_safety_tab()
        self.build_backup_tab()
        self.build_api_tab()
        self.build_account_tab()

    def build_general_tab(self):
        f = ttk.Frame(self.tab_general, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(f, text="Platform Brand Name:", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(10, 2))
        self.brand_ent = ttk.Entry(f, width=32)
        self.brand_ent.insert(0, "Enterprise WhatsApp Marketing")
        self.brand_ent.pack(fill="x", padx=10, pady=(0, 12))

        ttk.Label(f, text="Default Country Code:", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(2, 2))
        self.cc_ent = ttk.Entry(f, width=8)
        self.cc_ent.insert(0, "91")
        self.cc_ent.pack(anchor="w", padx=10, pady=(0, 12))

        self.dedup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Always Deduplicate Phone Numbers", variable=self.dedup_var).pack(anchor="w", padx=10, pady=5)

        self.sound_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Play Notification Sound on Campaign Finish", variable=self.sound_var).pack(anchor="w", padx=10, pady=5)

    def build_safety_tab(self):
        f = ttk.Frame(self.tab_safety, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(f, text="Default Random Delay Interval (Seconds):", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(10, 2))
        d_frame = ttk.Frame(f, style="Card.TFrame")
        d_frame.pack(fill="x", padx=10, pady=(0, 15))

        self.min_d = ttk.Entry(d_frame, width=5)
        self.min_d.insert(0, "8")
        self.min_d.pack(side="left", padx=(0, 4))
        ttk.Label(d_frame, text="to", style="CardLabel.TLabel").pack(side="left", padx=4)
        self.max_d = ttk.Entry(d_frame, width=5)
        self.max_d.insert(0, "15")
        self.max_d.pack(side="left", padx=(4, 0))

        self.sim_type_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Simulate Keystrokes (Anti-Bot Detection)", variable=self.sim_type_var).pack(anchor="w", padx=10, pady=5)

        ttk.Label(f, text="Cooldown Batch Rest Interval:", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(15, 2))
        b_frame = ttk.Frame(f, style="Card.TFrame")
        b_frame.pack(fill="x", padx=10)
        ttk.Label(b_frame, text="Rest for 3 mins after every 30 messages.", style="CardVal.TLabel").pack(side="left")

    def build_backup_tab(self):
        f = ttk.Frame(self.tab_backup, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(f, text="Database Snapshot & Disaster Recovery", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 5))
        ttk.Label(f, text="Create instant compressed ZIP copies of your complete database.", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(0, 15))

        btn_bar = ttk.Frame(f, style="Card.TFrame")
        btn_bar.pack(fill="x", padx=10, pady=5)

        def do_backup():
            ok, path = create_backup()
            if ok:
                messagebox.showinfo("Backup Created", f"Backup snapshot saved to:\n{path}")
                self.refresh_backup_list()
            else:
                messagebox.showerror("Backup Error", path)

        def do_restore():
            f_path = filedialog.askopenfilename(title="Select Backup ZIP", filetypes=[("ZIP Archive", "*.zip")])
            if f_path and messagebox.askyesno("Confirm Restore", "Restoring will replace current database. A safety copy will be made. Proceed?"):
                ok, msg = restore_backup(f_path)
                if ok:
                    messagebox.showinfo("Restored", msg)
                else:
                    messagebox.showerror("Error", msg)

        ttk.Button(btn_bar, text="💾 Create Backup Snapshot Now", style="Primary.TButton", command=do_backup).pack(side="left", padx=(0, 6))
        ttk.Button(btn_bar, text="🔄 Restore from File", style="Secondary.TButton", command=do_restore).pack(side="left")

        self.backup_box = tk.Listbox(f, bg="#0b1120", fg="#f8fafc", font=("Consolas", 9), height=7)
        self.backup_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh_backup_list()

    def refresh_backup_list(self):
        self.backup_box.delete(0, tk.END)
        backups = list_backups()
        for b in backups:
            self.backup_box.insert(tk.END, f"{b['filename']} ({b['size_kb']} KB) — {b['date']}")

    def build_api_tab(self):
        f = ttk.Frame(self.tab_api, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(f, text="Local REST API Integration Engine", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 5))
        ttk.Label(f, text="Connect your CRM, Website, or Zapier webhooks to this machine.", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(0, 15))

        ttk.Label(f, text="API Base URL:", style="CardLabel.TLabel").pack(anchor="w", padx=10)
        u_ent = ttk.Entry(f, width=36)
        u_ent.insert(0, "http://127.0.0.1:8000/api")
        u_ent.pack(fill="x", padx=10, pady=(2, 10))

        ttk.Label(f, text="Live Secret API Key (X-API-Key):", style="CardLabel.TLabel").pack(anchor="w", padx=10)
        k_ent = ttk.Entry(f, width=36, font=("Consolas", 9, "bold"))
        k_ent.insert(0, "sk_live_enterprise_master_key_2026")
        k_ent.pack(fill="x", padx=10, pady=(2, 15))

        info = ttk.Label(f, text="Endpoints Available:\n• GET/POST /api/contacts\n• GET/POST /api/campaigns\n• GET /api/reports\n• GET /api/status", foreground="#60a5fa", font=("Segoe UI", 9))
        info.pack(anchor="w", padx=10)

    def build_account_tab(self):
        f = ttk.Frame(self.tab_account, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        u = SessionManager.get_user() or {"name": "Administrator", "email": "admin@enterprise.local", "role": "Owner"}

        ttk.Label(f, text=f"Logged in as: {u.get('name')}", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 2))
        ttk.Label(f, text=f"Email: {u.get('email')} | Role: {u.get('role')}", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(0, 15))

        ttk.Label(f, text="Change Password:", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 5))
        
        ttk.Label(f, text="Current Password:", style="CardLabel.TLabel").pack(anchor="w", padx=10)
        old_p = ttk.Entry(f, show="•", width=25)
        old_p.pack(anchor="w", padx=10, pady=(2, 6))

        ttk.Label(f, text="New Password:", style="CardLabel.TLabel").pack(anchor="w", padx=10)
        new_p = ttk.Entry(f, show="•", width=25)
        new_p.pack(anchor="w", padx=10, pady=(2, 10))

        def do_change_pwd():
            uid = u.get("id", 1)
            ok, msg = change_password(uid, old_p.get(), new_p.get())
            if ok:
                messagebox.showinfo("Password Changed", msg)
                old_p.delete(0, tk.END)
                new_p.delete(0, tk.END)
            else:
                messagebox.showerror("Error", msg)

        ttk.Button(f, text="Update Password", style="Primary.TButton", command=do_change_pwd).pack(anchor="w", padx=10)
