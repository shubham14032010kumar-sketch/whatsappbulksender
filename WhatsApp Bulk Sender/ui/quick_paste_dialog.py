"""
Direct Paste Numbers Dialog (ui/quick_paste_dialog.py)
Allows users to paste raw phone numbers directly (from WhatsApp, Notepad, or Websites)
without creating or formatting an Excel/CSV file.
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import pandas as pd
except ImportError:
    pd = None


class DirectPasteNumbersDialog:
    """1-Click Quick Paste Numbers Dialog for Fast Campaign Setup."""

    def __init__(self, parent, on_load_callback):
        self.top = tk.Toplevel(parent)
        self.top.title("📋 Quick Paste Numbers — Fast Broadcast Setup")
        self.top.geometry("560x520")
        self.top.minsize(500, 450)
        self.top.configure(bg="#090d16")
        self.top.transient(parent)
        self.top.grab_set()

        self.on_load_callback = on_load_callback
        self.build_ui()

    def build_ui(self):
        h_frame = ttk.Frame(self.top)
        h_frame.pack(fill="x", padx=20, pady=(15, 8))

        ttk.Label(h_frame, text="📋 Quick Paste Numbers", style="Header.TLabel").pack(side="left")
        ttk.Label(h_frame, text="NO EXCEL REQUIRED", style="StatGreen.TLabel").pack(side="right")

        ttk.Label(
            self.top,
            text="Paste your list of numbers below (one per line or comma-separated).\nNumbers will be automatically cleaned and loaded into the Campaign Queue.",
            style="CardLabel.TLabel"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        container = ttk.Frame(self.top, style="Card.TFrame")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 10), ipady=5, ipadx=5)

        # Settings row
        s_row = ttk.Frame(container, style="Card.TFrame")
        s_row.pack(fill="x", padx=10, pady=(5, 8))

        ttk.Label(s_row, text="Default Fallback Name:", style="CardLabel.TLabel").pack(side="left")
        self.name_entry = ttk.Entry(s_row, width=16)
        self.name_entry.insert(0, "Customer")
        self.name_entry.pack(side="left", padx=(4, 15))

        ttk.Label(s_row, text="Auto Country Code:", style="CardLabel.TLabel").pack(side="left")
        self.cc_entry = ttk.Entry(s_row, width=5)
        self.cc_entry.insert(0, "91")
        self.cc_entry.pack(side="left", padx=4)

        # Textarea
        ttk.Label(container, text="Paste Mobile Numbers Here:", style="CardLabel.TLabel").pack(anchor="w", padx=10)
        self.text_box = tk.Text(container, height=12, bg="#050811", fg="#e5e7eb", insertbackground="#fff", font=("Consolas", 10), relief="flat")
        self.text_box.pack(fill="both", expand=True, padx=10, pady=5)
        self.text_box.insert(tk.END, "9835012345\n9431098765\n8877665544\n")

        # Bottom buttons
        b_frame = ttk.Frame(self.top)
        b_frame.pack(fill="x", padx=20, pady=(0, 15))

        ttk.Button(b_frame, text="🚀 Load Into Campaign Queue", style="Primary.TButton", command=self.process_and_load).pack(side="left")
        ttk.Button(b_frame, text="Cancel", style="Secondary.TButton", command=self.top.destroy).pack(side="right")

    def process_and_load(self):
        raw_content = self.text_box.get("1.0", tk.END).strip()
        if not raw_content:
            messagebox.showwarning("Empty Input", "Please paste at least one phone number.")
            return

        cc = self.cc_entry.get().strip()
        default_name = self.name_entry.get().strip() or "Customer"

        # Split by newlines, commas, or semicolons
        tokens = re.split(r'[\r\n,;]+', raw_content)
        valid_phones = []
        seen = set()

        for tok in tokens:
            digits = re.sub(r'[^\d]', '', tok.strip())
            if not digits:
                continue

            # Standardize 10 digits to country code
            if len(digits) == 10 and digits[0] in "6789" and cc:
                digits = f"{cc}{digits}"
            elif len(digits) == 11 and digits.startswith("0") and cc:
                digits = f"{cc}{digits[1:]}"

            if len(digits) >= 10 and digits not in seen:
                seen.add(digits)
                valid_phones.append(digits)

        if not valid_phones:
            messagebox.showerror("No Valid Numbers", "Could not find any valid mobile numbers in the pasted text.")
            return

        if pd is not None:
            df = pd.DataFrame({
                "Phone": valid_phones,
                "Name": [default_name] * len(valid_phones)
            })
        else:
            # Fallback mock dataframe object if pandas not installed
            class SimpleDF:
                def __init__(self, data):
                    self.data = data
                    self.columns = list(data.keys())
                def __len__(self):
                    return len(self.data["Phone"])
                def to_dict(self, orient="records"):
                    rows = []
                    for i in range(len(self)):
                        rows.append({k: self.data[k][i] for k in self.columns})
                    return rows
            df = SimpleDF({"Phone": valid_phones, "Name": [default_name] * len(valid_phones)})

        self.on_load_callback(df, count=len(valid_phones))
        self.top.destroy()
