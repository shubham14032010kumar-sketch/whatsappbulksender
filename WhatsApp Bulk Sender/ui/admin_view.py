"""
Super Admin Panel View (ui/admin_view.py)
Administrative control center for Users, Customers, Licenses,
Plans, Usage metrics, and System Audit Logs.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from core.auth import get_all_users, register_user, delete_user
from core.licensing import get_plan_limits, generate_commercial_key
from core.audit import get_audit_logs
from core.analytics import get_dashboard_metrics
from core.db import get_connection


class AdminPanelFrame(ttk.Frame):
    """Super Admin Panel Container with sub-tabs."""

    def __init__(self, parent):
        super().__init__(parent, style="TFrame")
        self.pack(fill="both", expand=True, padx=15, pady=12)

        # Header Title
        h_frame = ttk.Frame(self, style="TFrame")
        h_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(h_frame, text="⚙️ Master Admin Control Center", style="Header.TLabel").pack(side="left")
        ttk.Label(h_frame, text="RESTRICTED TO OWNER & ADMIN ROLES", style="StatRed.TLabel").pack(side="right")

        # Admin Sub-notebook
        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill="both", expand=True)

        self.tab_dash = ttk.Frame(self.sub_notebook, style="TFrame")
        self.tab_users = ttk.Frame(self.sub_notebook, style="TFrame")
        self.tab_licenses = ttk.Frame(self.sub_notebook, style="TFrame")
        self.tab_audit = ttk.Frame(self.sub_notebook, style="TFrame")

        self.sub_notebook.add(self.tab_dash, text="📊 Platform Overview")
        self.sub_notebook.add(self.tab_users, text="👥 Team & Users")
        self.sub_notebook.add(self.tab_licenses, text="🔑 License Control")
        self.sub_notebook.add(self.tab_audit, text="📋 System Audit Logs")

        self.build_overview_tab()
        self.build_users_tab()
        self.build_licenses_tab()
        self.build_audit_tab()

    # --- 1. OVERVIEW ---
    def build_overview_tab(self):
        m = get_dashboard_metrics()
        container = ttk.Frame(self.tab_dash, style="Card.TFrame")
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(container, text="Platform KPIs & Performance Metrics", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 12))

        grid = ttk.Frame(container, style="Card.TFrame")
        grid.pack(fill="x", padx=10, pady=5)

        cards = [
            ("Total Contacts in DB", str(m["total_contacts"]), "StatBlue.TLabel"),
            ("Total Campaigns Created", str(m["total_campaigns"]), "StatGreen.TLabel"),
            ("Messages Delivered", str(m["total_sent"]), "StatGreen.TLabel"),
            ("Messages Failed", str(m["total_failed"]), "StatRed.TLabel"),
            ("Customer Opt-Outs", str(m["opt_outs"]), "StatYellow.TLabel"),
            ("Success Rate", f"{m['success_rate']}%", "StatBlue.TLabel")
        ]

        for idx, (title, val, style_name) in enumerate(cards):
            r = idx // 3
            c = idx % 3
            f = ttk.Frame(grid, style="Card.TFrame")
            f.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            grid.columnconfigure(c, weight=1)
            ttk.Label(f, text=title, style="CardLabel.TLabel").pack(anchor="w")
            ttk.Label(f, text=val, style=style_name).pack(anchor="w", pady=(4, 0))

    # --- 2. USERS TAB ---
    def build_users_tab(self):
        container = ttk.Frame(self.tab_users, style="Card.TFrame")
        container.pack(fill="both", expand=True, padx=15, pady=15)

        btn_bar = ttk.Frame(container, style="Card.TFrame")
        btn_bar.pack(fill="x", padx=10, pady=(5, 10))

        ttk.Label(btn_bar, text="User & Team Access Management", style="CardTitle.TLabel").pack(side="left")
        ttk.Button(btn_bar, text="➕ Add User", style="Primary.TButton", command=self.add_user_dialog).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="🗑️ Remove User", style="Danger.TButton", command=self.delete_user_action).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="🔄 Refresh", style="Secondary.TButton", command=self.refresh_users_tree).pack(side="right", padx=4)

        tree_frame = ttk.Frame(container, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("ID", "Name", "Email", "Role", "Status", "Created")
        self.user_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for col in cols:
            self.user_tree.heading(col, text=col)
            self.user_tree.column(col, width=120)
        self.user_tree.column("ID", width=45)
        self.user_tree.column("Email", width=220)
        self.user_tree.pack(side="left", fill="both", expand=True)

        self.refresh_users_tree()

    def refresh_users_tree(self):
        for r in self.user_tree.get_children():
            self.user_tree.delete(r)
        users = get_all_users()
        for u in users:
            self.user_tree.insert("", tk.END, values=(u["id"], u["name"], u["email"], u["role"], u["status"], u["created_at"]))

    def add_user_dialog(self):
        top = tk.Toplevel(self)
        top.title("Add Team Member")
        top.geometry("380x320")
        top.configure(bg="#090d16")

        ttk.Label(top, text="Create Team Member Account", style="CardTitle.TLabel").pack(pady=10)
        f = ttk.Frame(top, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        ttk.Label(f, text="Name:", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(6, 2))
        n_entry = ttk.Entry(f, width=28)
        n_entry.pack(fill="x", padx=10)

        ttk.Label(f, text="Email:", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(6, 2))
        e_entry = ttk.Entry(f, width=28)
        e_entry.pack(fill="x", padx=10)

        ttk.Label(f, text="Role:", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(6, 2))
        r_var = tk.StringVar(value="Staff")
        r_combo = ttk.Combobox(f, textvariable=r_var, values=["Admin", "Manager", "Staff"], state="readonly")
        r_combo.pack(fill="x", padx=10)

        ttk.Label(f, text="Password:", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(6, 2))
        p_entry = ttk.Entry(f, width=28, show="•")
        p_entry.pack(fill="x", padx=10)

        def save():
            nm, em, pw, rl = n_entry.get().strip(), e_entry.get().strip(), p_entry.get().strip(), r_var.get()
            ok, res = register_user(nm, em, pw, role=rl)
            if ok:
                top.destroy()
                self.refresh_users_tree()
                messagebox.showinfo("User Added", f"Account created for {nm}!")
            else:
                messagebox.showerror("Error", res)

        ttk.Button(top, text="Save User", style="Primary.TButton", command=save).pack(pady=10)

    def delete_user_action(self):
        sel = self.user_tree.selection()
        if not sel:
            messagebox.showwarning("Select User", "Select a user to remove.")
            return
        uid = self.user_tree.item(sel[0])["values"][0]
        if uid == 1:
            messagebox.showerror("Cannot Delete", "Primary Owner account cannot be deleted.")
            return
        if messagebox.askyesno("Confirm Delete", "Remove this user account?"):
            delete_user(uid)
            self.refresh_users_tree()

    # --- 3. LICENSES TAB ---
    def build_licenses_tab(self):
        container = ttk.Frame(self.tab_licenses, style="Card.TFrame")
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(container, text="🔑 Customer License Generator & Issuer", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 5))
        ttk.Label(container, text="Generate commercial keys for clients (₹499 Starter, ₹1,999 Pro, ₹4,999 Business)", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(0, 10))

        form = ttk.Frame(container, style="Card.TFrame")
        form.pack(fill="x", padx=10, pady=5)

        ttk.Label(form, text="Client Machine ID (or GLOBAL):", style="CardLabel.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        mach_entry = ttk.Entry(form, width=20)
        mach_entry.insert(0, "GLOBAL")
        mach_entry.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(form, text="Plan:", style="CardLabel.TLabel").grid(row=0, column=2, sticky="w", padx=(15, 0), pady=4)
        p_var = tk.StringVar(value="Pro")
        p_combo = ttk.Combobox(form, textvariable=p_var, values=["Starter", "Pro", "Business"], state="readonly", width=12)
        p_combo.grid(row=0, column=3, sticky="w", padx=8, pady=4)

        ttk.Label(form, text="Duration (Days):", style="CardLabel.TLabel").grid(row=0, column=4, sticky="w", padx=(15, 0), pady=4)
        d_entry = ttk.Entry(form, width=8)
        d_entry.insert(0, "365")
        d_entry.grid(row=0, column=5, sticky="w", padx=8, pady=4)

        out_var = tk.StringVar()
        out_entry = ttk.Entry(container, textvariable=out_var, font=("Consolas", 11, "bold"), state="readonly")
        out_entry.pack(fill="x", padx=10, pady=(12, 6))

        def gen():
            m = mach_entry.get().strip().upper() or "GLOBAL"
            p = p_var.get()
            d = int(d_entry.get().strip() or "365")
            key = generate_commercial_key(p, d, m)
            out_var.set(key)

        def copy():
            k = out_var.get()
            if k:
                self.clipboard_clear()
                self.clipboard_append(k)
                messagebox.showinfo("Copied", "Commercial key copied to clipboard!")

        btn_row = ttk.Frame(container, style="Card.TFrame")
        btn_row.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_row, text="⚡ Generate Key", style="Primary.TButton", command=gen).pack(side="left", padx=4)
        ttk.Button(btn_row, text="📋 Copy Key", style="Secondary.TButton", command=copy).pack(side="left", padx=4)

        gen()

    # --- 4. AUDIT LOGS TAB ---
    def build_audit_tab(self):
        container = ttk.Frame(self.tab_audit, style="Card.TFrame")
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(container, text="Chronological System Audit Trail (Who / What / When)", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 10))

        tree_frame = ttk.Frame(container, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("Timestamp", "User", "Action", "Target", "Details")
        self.audit_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.audit_tree.heading("Timestamp", text="When (Date/Time)")
        self.audit_tree.heading("User", text="Who (User)")
        self.audit_tree.heading("Action", text="What (Action)")
        self.audit_tree.heading("Target", text="Target")
        self.audit_tree.heading("Details", text="Details")

        self.audit_tree.column("Timestamp", width=140)
        self.audit_tree.column("User", width=120)
        self.audit_tree.column("Action", width=180)
        self.audit_tree.column("Target", width=100)
        self.audit_tree.column("Details", width=300)
        self.audit_tree.pack(side="left", fill="both", expand=True)

        self.refresh_audit_tree()

    def refresh_audit_tree(self):
        for r in self.audit_tree.get_children():
            self.audit_tree.delete(r)
        logs = get_audit_logs(limit=100)
        for l in logs:
            self.audit_tree.insert("", tk.END, values=(l["timestamp"], l["user_name"], l["action"], f"{l['target_type']}:{l['target_id']}", l["details"]))
