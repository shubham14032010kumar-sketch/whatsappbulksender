"""
License Key Generator (Admin Tool)
Used by the software vendor/admin to generate customer activation keys.
Can be executed directly via terminal or run as a standalone desktop utility:
    python license_generator.py
"""

import sys
import argparse
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

import license_manager


def generate_key(plan="PRO", days_valid=365, machine_id="GLOBAL"):
    """Generates a cryptographic license key string."""
    machine_id = str(machine_id).strip().upper() or "GLOBAL"
    plan = str(plan).strip().upper()
    exp_date = datetime.now() + timedelta(days=int(days_valid))
    expiry_str = exp_date.strftime("%Y%m%d")
    sig = license_manager.generate_license_signature(plan, expiry_str, machine_id)
    return f"WBS-{plan}-{expiry_str}-{machine_id}-{sig}"


def run_gui():
    """Launches interactive generator GUI for admin."""
    root = tk.Tk()
    root.title("WhatsApp Bulk Sender — Key Generator (Admin Tool)")
    root.geometry("540x440")
    root.configure(bg="#0f172a")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background="#0f172a", foreground="#f8fafc", font=("Segoe UI", 9))
    style.configure("Header.TLabel", background="#0f172a", foreground="#38bdf8", font=("Segoe UI", 13, "bold"))
    style.configure("Primary.TButton", background="#10b981", foreground="#ffffff", font=("Segoe UI", 10, "bold"))

    ttk.Label(root, text="🔑 Commercial License Key Generator", style="Header.TLabel").pack(pady=(15, 5))
    ttk.Label(root, text="Generate hardware-locked or global keys for paying clients", foreground="#94a3b8").pack(pady=(0, 15))

    frame = ttk.Frame(root, style="TFrame")
    frame.pack(fill="x", padx=30)

    # Machine ID
    ttk.Label(frame, text="Customer Machine ID (or 'GLOBAL' for any PC):").pack(anchor="w", pady=(5, 2))
    mach_var = tk.StringVar(value="GLOBAL")
    mach_entry = ttk.Entry(frame, textvariable=mach_var, font=("Consolas", 10))
    mach_entry.pack(fill="x", pady=(0, 10))

    # Plan
    ttk.Label(frame, text="Plan Tier:").pack(anchor="w", pady=(5, 2))
    plan_var = tk.StringVar(value="PRO")
    plan_combo = ttk.Combobox(frame, textvariable=plan_var, values=["PRO", "BUSINESS"], state="readonly")
    plan_combo.pack(fill="x", pady=(0, 10))

    # Validity
    ttk.Label(frame, text="Validity Duration:").pack(anchor="w", pady=(5, 2))
    days_var = tk.StringVar(value="365")
    validity_combo = ttk.Combobox(frame, textvariable=days_var, values=["30", "90", "180", "365", "730", "1825"], state="normal")
    validity_combo.pack(fill="x", pady=(0, 15))

    # Output Key
    ttk.Label(frame, text="Generated Activation Key:").pack(anchor="w", pady=(5, 2))
    out_var = tk.StringVar()
    out_entry = ttk.Entry(frame, textvariable=out_var, font=("Consolas", 10, "bold"), state="readonly")
    out_entry.pack(fill="x", pady=(0, 15))

    def on_generate():
        try:
            m_id = mach_var.get().strip().upper() or "GLOBAL"
            p = plan_var.get().strip().upper()
            d = int(days_var.get().strip())
            key = generate_key(p, d, m_id)
            out_var.set(key)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate key: {str(e)}")

    def on_copy():
        k = out_var.get().strip()
        if k:
            root.clipboard_clear()
            root.clipboard_append(k)
            messagebox.showinfo("Copied", "License key copied to clipboard!")

    btn_frame = ttk.Frame(root)
    btn_frame.pack(pady=10)

    ttk.Button(btn_frame, text="⚡ Generate Key", style="Primary.TButton", command=on_generate).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="📋 Copy Key", command=on_copy).pack(side="left", padx=5)

    on_generate()
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Generate commercial license key")
        parser.add_argument("--plan", default="PRO", choices=["PRO", "BUSINESS"], help="Plan tier")
        parser.add_argument("--days", type=int, default=365, help="Validity in days")
        parser.add_argument("--machine", default="GLOBAL", help="Machine ID or GLOBAL")
        args = parser.parse_args()

        generated = generate_key(args.plan, args.days, args.machine)
        print(f"\n==========================================")
        print(f"Generated License Key: {generated}")
        print(f"Plan: {args.plan} | Valid: {args.days} days | Machine: {args.machine}")
        print(f"==========================================\n")
    else:
        run_gui()
