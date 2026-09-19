"""
Advanced CRM & Audience Segmentation Workspace (ui/crm_view.py)
Implements All Contacts, Groups, Tags, Custom Fields, Multi-Filter Segmentation,
and 1-Click Transfer to Campaign Builder.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
import json

from core.crm import (
    filter_contacts, add_or_update_contact, bulk_import_contacts,
    get_crm_kpis, get_all_groups, create_group, get_all_tags, create_tag,
    get_unique_values, delete_contacts, CONTACT_STATUSES
)
from core.audit import log_audit

try:
    import pandas as pd
except ImportError:
    pd = None


class CrmWorkspaceFrame(ttk.Frame):
    """Complete Enterprise CRM Interface."""

    def __init__(self, parent, on_transfer_to_campaign=None):
        super().__init__(parent, style="TFrame")
        self.pack(fill="both", expand=True, padx=15, pady=10)
        self.on_transfer = on_transfer_to_campaign
        self.filtered_cache = []

        # 1. Top KPI Summary Cards
        self.build_kpi_bar()

        # 2. Audience Segmentation & Filter Bar
        self.build_filter_bar()

        # 3. Contacts Data Table & Action Controls
        self.build_table_section()

        self.refresh_filters()
        self.refresh_table()

    def build_kpi_bar(self):
        kpis_frame = ttk.Frame(self, style="Card.TFrame")
        kpis_frame.pack(fill="x", pady=(0, 10), ipady=6, ipadx=10)

        self.kpi_total = ttk.Label(kpis_frame, text="Total Contacts: 0", style="StatBlue.TLabel")
        self.kpi_total.pack(side="left", expand=True, fill="x", padx=4)

        self.kpi_opted = ttk.Label(kpis_frame, text="Opted-in: 0", style="StatGreen.TLabel")
        self.kpi_opted.pack(side="left", expand=True, fill="x", padx=4)

        self.kpi_cities = ttk.Label(kpis_frame, text="Cities: 0", style="StatYellow.TLabel")
        self.kpi_cities.pack(side="left", expand=True, fill="x", padx=4)

        self.kpi_cats = ttk.Label(kpis_frame, text="Categories: 0", style="StatPurple.TLabel")
        self.kpi_cats.pack(side="left", expand=True, fill="x", padx=4)

        self.kpi_match = ttk.Label(kpis_frame, text="Segment Audience: 0", style="StatBlue.TLabel")
        self.kpi_match.pack(side="left", expand=True, fill="x", padx=4)

    def build_filter_bar(self):
        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(fill="x", pady=(0, 10), ipady=8, ipadx=10)

        ttk.Label(card, text="🎯 Multi-Parameter Audience Segmentation", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(2, 6))

        row1 = ttk.Frame(card, style="Card.TFrame")
        row1.pack(fill="x", padx=10, pady=2)

        # City
        ttk.Label(row1, text="City:", style="CardLabel.TLabel").pack(side="left")
        self.city_var = tk.StringVar(value="All Cities")
        self.city_combo = ttk.Combobox(row1, textvariable=self.city_var, state="readonly", width=13)
        self.city_combo.pack(side="left", padx=(4, 10))
        self.city_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        # Category
        ttk.Label(row1, text="Category:", style="CardLabel.TLabel").pack(side="left")
        self.cat_var = tk.StringVar(value="All Categories")
        self.cat_combo = ttk.Combobox(row1, textvariable=self.cat_var, state="readonly", width=14)
        self.cat_combo.pack(side="left", padx=(4, 10))
        self.cat_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        # Tag
        ttk.Label(row1, text="Tag:", style="CardLabel.TLabel").pack(side="left")
        self.tag_var = tk.StringVar(value="All Tags")
        self.tag_combo = ttk.Combobox(row1, textvariable=self.tag_var, state="readonly", width=13)
        self.tag_combo.pack(side="left", padx=(4, 10))
        self.tag_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        # Status
        ttk.Label(row1, text="Status:", style="CardLabel.TLabel").pack(side="left")
        self.status_var = tk.StringVar(value="All Statuses")
        self.status_combo = ttk.Combobox(row1, textvariable=self.status_var, state="readonly", width=13)
        self.status_combo.pack(side="left", padx=(4, 10))
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        # Search Query
        ttk.Label(row1, text="Search:", style="CardLabel.TLabel").pack(side="left")
        self.search_ent = ttk.Entry(row1, width=16)
        self.search_ent.pack(side="left", padx=(4, 8))
        self.search_ent.bind("<KeyRelease>", lambda e: self.refresh_table())

        ttk.Button(row1, text="🔄 Reset", style="Secondary.TButton", command=self.reset_filters).pack(side="left", padx=2)

    def build_table_section(self):
        container = ttk.Frame(self, style="Card.TFrame")
        container.pack(fill="both", expand=True, ipady=6, ipadx=10)

        # Action Buttons row
        action_row = ttk.Frame(container, style="Card.TFrame")
        action_row.pack(fill="x", padx=10, pady=(6, 8))

        ttk.Button(action_row, text="📥 Import Excel/CSV", style="Primary.TButton", command=self.import_contacts_dialog).pack(side="left", padx=(0, 4))
        ttk.Button(action_row, text="➕ Add Contact", style="Secondary.TButton", command=self.add_contact_dialog).pack(side="left", padx=4)
        ttk.Button(action_row, text="🏷️ Manage Tags", style="Secondary.TButton", command=self.manage_tags_dialog).pack(side="left", padx=4)
        ttk.Button(action_row, text="👥 Manage Groups", style="Secondary.TButton", command=self.manage_groups_dialog).pack(side="left", padx=4)
        ttk.Button(action_row, text="🗑️ Delete Selected", style="Danger.TButton", command=self.delete_selected).pack(side="left", padx=4)
        ttk.Button(action_row, text="📤 Export CSV", style="Secondary.TButton", command=self.export_csv).pack(side="left", padx=4)

        # Key Feature Transfer Button
        self.btn_transfer = ttk.Button(
            action_row,
            text="🚀 SEND CAMPAIGN TO FILTERED AUDIENCE",
            style="ActionBlue.TButton",
            command=self.transfer_to_campaign
        )
        self.btn_transfer.pack(side="right", padx=2)

        # Treeview
        tree_frame = ttk.Frame(container, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=4)

        cols = ("ID", "Name", "Phone", "Email", "Company", "City", "Category", "Tags", "Status", "Opt-in", "Notes")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")

        col_widths = {
            "ID": 45, "Name": 130, "Phone": 120, "Email": 130, "Company": 120,
            "City": 90, "Category": 100, "Tags": 120, "Status": 90, "Opt-in": 60, "Notes": 140
        }
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=col_widths.get(c, 100))

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def refresh_filters(self):
        kpis = get_crm_kpis()
        self.kpi_total.config(text=f"Total: {kpis['total_contacts']}")
        self.kpi_opted.config(text=f"Opted-in: {kpis['opted_in']}")
        self.kpi_cities.config(text=f"Cities: {kpis['total_cities']}")
        self.kpi_cats.config(text=f"Categories: {kpis['total_categories']}")

        cities = ["All Cities"] + get_unique_values("city")
        cats = ["All Categories"] + get_unique_values("category")
        statuses = ["All Statuses"] + CONTACT_STATUSES
        tags = ["All Tags"] + [t["name"] for t in get_all_tags()]

        self.city_combo['values'] = cities
        if self.city_var.get() not in cities:
            self.city_var.set("All Cities")

        self.cat_combo['values'] = cats
        if self.cat_var.get() not in cats:
            self.cat_var.set("All Categories")

        self.tag_combo['values'] = tags
        if self.tag_var.get() not in tags:
            self.tag_var.set("All Tags")

        self.status_combo['values'] = statuses
        if self.status_var.get() not in statuses:
            self.status_var.set("All Statuses")

    def refresh_table(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        city = self.city_var.get()
        cat = self.cat_var.get()
        tag = self.tag_var.get()
        status = self.status_var.get()
        search = self.search_ent.get().strip()

        contacts = filter_contacts(city=city, category=cat, tag=tag, status=status, search=search)
        self.filtered_cache = contacts
        self.kpi_match.config(text=f"Segment Audience: {len(contacts)}")

        for c in contacts:
            opt_str = "Yes" if c.get("opt_in") == 1 else "No"
            vals = (
                c.get("id"), c.get("name"), c.get("phone"), c.get("email"),
                c.get("company"), c.get("city"), c.get("category"), c.get("tags"),
                c.get("status"), opt_str, c.get("notes")
            )
            self.tree.insert("", tk.END, values=vals)

    def reset_filters(self):
        self.city_var.set("All Cities")
        self.cat_var.set("All Categories")
        self.tag_var.set("All Tags")
        self.status_var.set("All Statuses")
        self.search_ent.delete(0, tk.END)
        self.refresh_table()

    def add_contact_dialog(self):
        top = tk.Toplevel(self)
        top.title("Add Contact to CRM")
        top.geometry("440x500")
        top.configure(bg="#090d16")

        ttk.Label(top, text="👤 Add New CRM Lead / Contact", style="CardTitle.TLabel").pack(pady=10)
        f = ttk.Frame(top, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        fields = [
            ("Phone / WhatsApp (*):", "phone"),
            ("Full Name:", "name"),
            ("Email Address:", "email"),
            ("Company / Hotel / School:", "company"),
            ("City:", "city"),
            ("Category (e.g. Hotel, Doctor):", "category"),
            ("Tags (comma separated):", "tags"),
            ("Notes / Address:", "notes")
        ]
        entries = {}
        for idx, (label_txt, k) in enumerate(fields):
            ttk.Label(f, text=label_txt, style="CardLabel.TLabel").grid(row=idx, column=0, sticky="w", padx=10, pady=3)
            e = ttk.Entry(f, width=28)
            e.grid(row=idx, column=1, sticky="w", padx=10, pady=3)
            entries[k] = e

        ttk.Label(f, text="Status:", style="CardLabel.TLabel").grid(row=len(fields), column=0, sticky="w", padx=10, pady=3)
        st_var = tk.StringVar(value="New Lead")
        st_combo = ttk.Combobox(f, textvariable=st_var, values=CONTACT_STATUSES, state="readonly", width=25)
        st_combo.grid(row=len(fields), column=1, sticky="w", padx=10, pady=3)

        def save():
            ph = entries["phone"].get().strip()
            if not ph:
                messagebox.showwarning("Phone Required", "Phone number is mandatory.")
                return
            ok, cid = add_or_update_contact(
                entries["name"].get(), ph, email=entries["email"].get(),
                company=entries["company"].get(), city=entries["city"].get(),
                category=entries["category"].get(), tags=entries["tags"].get(),
                notes=entries["notes"].get(), status=st_var.get()
            )
            if ok:
                top.destroy()
                self.refresh_filters()
                self.refresh_table()
                messagebox.showinfo("Saved", f"Contact '{ph}' saved successfully!")
            else:
                messagebox.showerror("Error", cid)

        btn_row = ttk.Frame(top)
        btn_row.pack(pady=10)
        ttk.Button(btn_row, text="Save Contact", style="Primary.TButton", command=save).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=top.destroy).pack(side="left")

    def import_contacts_dialog(self):
        if not pd:
            messagebox.showerror("Pandas Required", "Pandas is required to import spreadsheets.")
            return

        f = filedialog.askopenfilename(
            title="Select Contacts File",
            filetypes=[("Excel & CSV", "*.xlsx *.xls *.csv"), ("CSV", "*.csv"), ("Excel", "*.xlsx *.xls")]
        )
        if not f:
            return

        try:
            df = pd.read_csv(f, dtype=str) if f.endswith(".csv") else pd.read_excel(f, dtype=str)
            if df.empty:
                messagebox.showwarning("Empty File", "File contains no rows.")
                return

            cols = list(df.columns)
            ph_col = next((c for c in cols if any(k in c.lower() for k in ["phone", "mobile", "contact", "number", "whatsapp"])), cols[0])
            nm_col = next((c for c in cols if any(k in c.lower() for k in ["name", "customer", "person"])), None)
            em_col = next((c for c in cols if "email" in c.lower()), None)
            comp_col = next((c for c in cols if any(k in c.lower() for k in ["company", "hotel", "org", "business"])), None)
            city_col = next((c for c in cols if any(k in c.lower() for k in ["city", "location", "town"])), None)
            cat_col = next((c for c in cols if any(k in c.lower() for k in ["category", "type", "industry"])), None)
            tag_col = next((c for c in cols if any(k in c.lower() for k in ["tag", "tags", "group"])), None)
            note_col = next((c for c in cols if any(k in c.lower() for k in ["note", "notes", "remark", "address"])), None)

            records = []
            for _, r in df.iterrows():
                records.append({
                    "name": str(r.get(nm_col, "") or "") if nm_col else "",
                    "phone": str(r.get(ph_col, "") or ""),
                    "email": str(r.get(em_col, "") or "") if em_col else "",
                    "company": str(r.get(comp_col, "") or "") if comp_col else "",
                    "city": str(r.get(city_col, "") or "") if city_col else "",
                    "category": str(r.get(cat_col, "") or "") if cat_col else "",
                    "tags": str(r.get(tag_col, "") or "") if tag_col else "",
                    "notes": str(r.get(note_col, "") or "") if note_col else ""
                })

            imported, errs = bulk_import_contacts(records)
            self.refresh_filters()
            self.refresh_table()
            messagebox.showinfo("Import Completed", f"Successfully imported {imported} contacts!\n(Skipped/Invalid: {errs})")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed: {str(e)}")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select at least one contact.")
            return
        ids = [self.tree.item(s)["values"][0] for s in sel]
        if messagebox.askyesno("Confirm Delete", f"Delete {len(ids)} contacts?"):
            delete_contacts(ids)
            self.refresh_filters()
            self.refresh_table()

    def export_csv(self):
        if not self.filtered_cache or not pd:
            messagebox.showinfo("No Data", "No contacts to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            df = pd.DataFrame(self.filtered_cache)
            df.to_csv(path, index=False)
            messagebox.showinfo("Exported", f"Saved {len(df)} contacts to '{path}'")

    def manage_tags_dialog(self):
        top = tk.Toplevel(self)
        top.title("Tags Manager")
        top.geometry("340x360")
        top.configure(bg="#090d16")

        ttk.Label(top, text="🏷️ Lead Warmth & Custom Tags", style="CardTitle.TLabel").pack(pady=10)
        box = tk.Listbox(top, bg="#0b1120", fg="#f8fafc", font=("Segoe UI", 10), height=8)
        box.pack(fill="both", expand=True, padx=15, pady=5)

        def load_tags():
            box.delete(0, tk.END)
            for t in get_all_tags():
                box.insert(tk.END, f"• {t['name']}")
        load_tags()

        f = ttk.Frame(top)
        f.pack(fill="x", padx=15, pady=10)
        e = ttk.Entry(f, width=20)
        e.pack(side="left", padx=4)
        def add_t():
            val = e.get().strip()
            if val:
                create_tag(val)
                e.delete(0, tk.END)
                load_tags()
                self.refresh_filters()
        ttk.Button(f, text="➕ Add Tag", style="Primary.TButton", command=add_t).pack(side="left")

    def manage_groups_dialog(self):
        top = tk.Toplevel(self)
        top.title("Groups Manager")
        top.geometry("380x380")
        top.configure(bg="#090d16")

        ttk.Label(top, text="👥 Industry & Audience Groups", style="CardTitle.TLabel").pack(pady=10)
        box = tk.Listbox(top, bg="#0b1120", fg="#f8fafc", font=("Segoe UI", 10), height=8)
        box.pack(fill="both", expand=True, padx=15, pady=5)

        def load_g():
            box.delete(0, tk.END)
            for g in get_all_groups():
                box.insert(tk.END, f"• {g['name']} ({g['member_count']} members)")
        load_g()

        f = ttk.Frame(top)
        f.pack(fill="x", padx=15, pady=10)
        e = ttk.Entry(f, width=22)
        e.pack(side="left", padx=4)
        def add_g():
            val = e.get().strip()
            if val:
                create_group(val)
                e.delete(0, tk.END)
                load_g()
                self.refresh_filters()
        ttk.Button(f, text="➕ Add Group", style="Primary.TButton", command=add_g).pack(side="left")

    def transfer_to_campaign(self):
        """Transfers filtered audience directly into Campaign Builder."""
        if not self.filtered_cache:
            messagebox.showwarning("Empty Audience", "Current filter matched 0 contacts. Adjust filters first.")
            return

        if self.on_transfer:
            self.on_transfer(self.filtered_cache)
