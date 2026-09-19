"""
Authentication & User Profile Dialogs (ui/auth_dialog.py)
Modal interfaces for Login, Registration, and Password Updates.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from core.auth import authenticate_user, register_user, change_password, SessionManager


class AuthLoginDialog:
    """User Login Modal Dialog."""

    def __init__(self, parent, on_success_callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("Enterprise User Login")
        self.top.geometry("400x340")
        self.top.configure(bg="#090d16")
        self.top.transient(parent)
        self.top.grab_set()

        self.on_success = on_success_callback

        ttk.Label(self.top, text="🔐 Enterprise Login", style="Header.TLabel").pack(pady=(20, 5))
        ttk.Label(self.top, text="Sign in to access your CRM & Campaigns", foreground="#94a3b8").pack(pady=(0, 15))

        card = ttk.Frame(self.top, style="Card.TFrame")
        card.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        ttk.Label(card, text="Email Address:", style="CardLabel.TLabel").pack(anchor="w", padx=15, pady=(12, 2))
        self.email_entry = ttk.Entry(card, width=32)
        self.email_entry.pack(fill="x", padx=15, pady=(0, 10))
        self.email_entry.insert(0, "admin@enterprise.local")

        ttk.Label(card, text="Password:", style="CardLabel.TLabel").pack(anchor="w", padx=15, pady=(2, 2))
        self.pass_entry = ttk.Entry(card, width=32, show="•")
        self.pass_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.pass_entry.insert(0, "admin123")

        btn_row = ttk.Frame(self.top)
        btn_row.pack(fill="x", padx=25, pady=(0, 15))

        ttk.Button(btn_row, text="Login ➔", style="Primary.TButton", command=self.do_login).pack(side="right", padx=4)
        ttk.Button(btn_row, text="Register New", style="Secondary.TButton", command=self.open_register).pack(side="left")

    def do_login(self):
        em = self.email_entry.get().strip()
        pw = self.pass_entry.get().strip()
        user, msg = authenticate_user(em, pw)
        if user:
            SessionManager.set_user(user)
            self.top.destroy()
            if self.on_success:
                self.on_success(user)
        else:
            messagebox.showerror("Login Failed", msg)

    def open_register(self):
        self.top.destroy()
        AuthRegisterDialog(self.top.master, self.on_success)


class AuthRegisterDialog:
    """New User Registration Modal Dialog."""

    def __init__(self, parent, on_success_callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("Register User Account")
        self.top.geometry("420x400")
        self.top.configure(bg="#090d16")
        self.top.transient(parent)
        self.top.grab_set()

        self.on_success = on_success_callback

        ttk.Label(self.top, text="👤 Register Account", style="Header.TLabel").pack(pady=(15, 5))
        ttk.Label(self.top, text="Create a new team member or admin account", foreground="#94a3b8").pack(pady=(0, 12))

        card = ttk.Frame(self.top, style="Card.TFrame")
        card.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        ttk.Label(card, text="Full Name:", style="CardLabel.TLabel").pack(anchor="w", padx=15, pady=(8, 2))
        self.name_entry = ttk.Entry(card, width=32)
        self.name_entry.pack(fill="x", padx=15, pady=(0, 6))

        ttk.Label(card, text="Email Address:", style="CardLabel.TLabel").pack(anchor="w", padx=15, pady=(2, 2))
        self.email_entry = ttk.Entry(card, width=32)
        self.email_entry.pack(fill="x", padx=15, pady=(0, 6))

        ttk.Label(card, text="Role:", style="CardLabel.TLabel").pack(anchor="w", padx=15, pady=(2, 2))
        self.role_var = tk.StringVar(value="Manager")
        self.role_combo = ttk.Combobox(card, textvariable=self.role_var, values=["Admin", "Manager", "Staff"], state="readonly")
        self.role_combo.pack(fill="x", padx=15, pady=(0, 6))

        ttk.Label(card, text="Password:", style="CardLabel.TLabel").pack(anchor="w", padx=15, pady=(2, 2))
        self.pass_entry = ttk.Entry(card, width=32, show="•")
        self.pass_entry.pack(fill="x", padx=15, pady=(0, 10))

        btn_row = ttk.Frame(self.top)
        btn_row.pack(fill="x", padx=25, pady=(0, 15))

        ttk.Button(btn_row, text="Create Account", style="Primary.TButton", command=self.do_register).pack(side="right", padx=4)
        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=self.top.destroy).pack(side="left")

    def do_register(self):
        nm = self.name_entry.get().strip()
        em = self.email_entry.get().strip()
        pw = self.pass_entry.get().strip()
        role = self.role_var.get()

        ok, res = register_user(nm, em, pw, role=role)
        if ok:
            messagebox.showinfo("Success", f"Account created for {nm} ({role})! Please log in.")
            self.top.destroy()
            AuthLoginDialog(self.top.master, self.on_success)
        else:
            messagebox.showerror("Error", res)
