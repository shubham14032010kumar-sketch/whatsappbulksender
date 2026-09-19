"""
Instagram & Public Lead Extractor Dialog (ui/lead_extractor_dialog.py)
Interactive UI for scraping and discovering high-converting local WhatsApp leads
by Niche & City with instant 1-Click transfer to Campaign Sender or CRM.
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

from core.lead_extractor import search_instagram_public_leads
from core.crm import add_or_update_contact

try:
    import pandas as pd
except ImportError:
    pd = None


class InstagramLeadExtractorDialog:
    """Modern Interactive Lead Generation Hub for Instagram & Public Local Directories."""

    POPULAR_NICHES = [
        "Gym & Fitness",
        "Boutiques & Fashion",
        "Real Estate & Property",
        "Coaching & Tuition Institutes",
        "Doctors & Dental Clinics",
        "Restaurants & Cafes",
        "Beauty Salons & Spa",
        "Car & Bike Showrooms",
        "Tour & Travel Agencies",
        "Digital Marketing Agencies"
    ]

    POPULAR_CITIES = [
        "Patna",
        "Delhi NCR",
        "Mumbai",
        "Bangalore",
        "Lucknow",
        "Jaipur",
        "Kolkata",
        "Ranchi",
        "Indore",
        "Varanasi"
    ]

    def __init__(self, parent, on_transfer_to_campaign=None):
        self.top = tk.Toplevel(parent)
        self.top.title("🎯 Instagram & Local Lead Extractor — Growth Engine")
        self.top.geometry("820x620")
        self.top.minsize(760, 520)
        self.top.configure(bg="#090d16")
        self.top.transient(parent)

        self.on_transfer_to_campaign = on_transfer_to_campaign
        self.extracted_leads = []
        self.is_searching = False

        self.build_ui()

    def build_ui(self):
        # 1. Header Frame
        h_frame = ttk.Frame(self.top)
        h_frame.pack(fill="x", padx=20, pady=(15, 10))

        title_lbl = ttk.Label(h_frame, text="🎯 Local Business & Instagram Lead Extractor", style="Header.TLabel")
        title_lbl.pack(side="left")

        sub_lbl = ttk.Label(h_frame, text="● PUBLIC SEARCH ENGINE", style="StatGreen.TLabel")
        sub_lbl.pack(side="right")

        desc_lbl = ttk.Label(
            self.top,
            text="Extract verified WhatsApp business numbers from public Instagram bios & local directories without account ban risks.",
            style="CardLabel.TLabel"
        )
        desc_lbl.pack(anchor="w", padx=20, pady=(0, 10))

        # 2. Controls Card
        ctrl_card = ttk.Frame(self.top, style="Card.TFrame")
        ctrl_card.pack(fill="x", padx=20, pady=(0, 10), ipady=8, ipadx=10)

        # Row 1: Niche + City + Count
        r1 = ttk.Frame(ctrl_card, style="Card.TFrame")
        r1.pack(fill="x", padx=10, pady=5)

        ttk.Label(r1, text="Business Niche / Keyword:", style="CardLabel.TLabel").grid(row=0, column=0, sticky="w", padx=5)
        self.niche_combo = ttk.Combobox(r1, values=self.POPULAR_NICHES, width=24)
        self.niche_combo.set(self.POPULAR_NICHES[0])
        self.niche_combo.grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(r1, text="Target City / Region:", style="CardLabel.TLabel").grid(row=0, column=2, sticky="w", padx=(15, 5))
        self.city_combo = ttk.Combobox(r1, values=self.POPULAR_CITIES, width=18)
        self.city_combo.set(self.POPULAR_CITIES[0])
        self.city_combo.grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(r1, text="Target Quantity:", style="CardLabel.TLabel").grid(row=0, column=4, sticky="w", padx=(15, 5))
        self.qty_combo = ttk.Combobox(r1, values=["15", "30", "50", "100"], state="readonly", width=6)
        self.qty_combo.set("30")
        self.qty_combo.grid(row=0, column=5, sticky="w", padx=5)

        # Row 2: Action Button & Progress
        r2 = ttk.Frame(ctrl_card, style="Card.TFrame")
        r2.pack(fill="x", padx=10, pady=(10, 5))

        self.btn_search = ttk.Button(r2, text="🔍 Start Lead Extraction", style="ActionBlue.TButton", command=self.start_extraction)
        self.btn_search.pack(side="left")

        self.status_lbl = ttk.Label(r2, text="Ready to search. Select niche & city above.", style="CardLabel.TLabel")
        self.status_lbl.pack(side="left", padx=15)

        # 3. Results Table Card
        table_card = ttk.Frame(self.top, style="Card.TFrame")
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 10), ipady=5, ipadx=5)

        tb_hdr = ttk.Frame(table_card, style="Card.TFrame")
        tb_hdr.pack(fill="x", padx=10, pady=(5, 5))

        self.results_count_lbl = ttk.Label(tb_hdr, text="Discovered Leads: 0", style="CardTitle.TLabel")
        self.results_count_lbl.pack(side="left")

        # Table Treeview
        tree_frame = ttk.Frame(table_card, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("#", "Name", "WhatsApp Phone", "City", "Category", "Source")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)
        self.tree.heading("#", text="#")
        self.tree.heading("Name", text="Business / Lead Name")
        self.tree.heading("WhatsApp Phone", text="WhatsApp Phone")
        self.tree.heading("City", text="City")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Source", text="Source")

        self.tree.column("#", width=40, anchor="center")
        self.tree.column("Name", width=180)
        self.tree.column("WhatsApp Phone", width=140, anchor="center")
        self.tree.column("City", width=100, anchor="center")
        self.tree.column("Category", width=140)
        self.tree.column("Source", width=140)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 4. Action Bottom Bar
        b_bar = ttk.Frame(self.top)
        b_bar.pack(fill="x", padx=20, pady=(0, 15))

        self.btn_send_campaign = ttk.Button(
            b_bar,
            text="🚀 Send Directly to Campaign Sender",
            style="Primary.TButton",
            command=self.transfer_to_campaign,
            state="disabled"
        )
        self.btn_send_campaign.pack(side="left", padx=(0, 8))

        self.btn_save_crm = ttk.Button(
            b_bar,
            text="💾 Save to CRM Database",
            style="Secondary.TButton",
            command=self.save_to_crm,
            state="disabled"
        )
        self.btn_save_crm.pack(side="left", padx=8)

        self.btn_export = ttk.Button(
            b_bar,
            text="📥 Export to CSV",
            style="Secondary.TButton",
            command=self.export_csv,
            state="disabled"
        )
        self.btn_export.pack(side="left", padx=8)

        ttk.Button(b_bar, text="Close", style="Secondary.TButton", command=self.top.destroy).pack(side="right")

    def start_extraction(self):
        if self.is_searching:
            return

        niche = self.niche_combo.get().strip()
        city = self.city_combo.get().strip()
        if not niche or not city:
            messagebox.showwarning("Missing Inputs", "Please enter both Niche and Target City.")
            return

        try:
            qty = int(self.qty_combo.get())
        except ValueError:
            qty = 30

        self.is_searching = True
        self.btn_search.config(state="disabled", text="⏳ Extracting Leads...")
        self.status_lbl.config(text="Contacting public search indexes...", style="StatYellow.TLabel")

        # Clear existing table
        for r in self.tree.get_children():
            self.tree.delete(r)
        self.extracted_leads = []

        thread = threading.Thread(target=self._search_worker, args=(niche, city, qty), daemon=True)
        thread.start()

    def _search_worker(self, niche, city, qty):
        def cb(msg, count):
            self.top.after(0, lambda: self.status_lbl.config(text=f"{msg} ({count} found)"))

        leads = search_instagram_public_leads(niche, city, max_results=qty, progress_callback=cb)
        self.top.after(0, lambda: self._on_search_completed(leads))

    def _on_search_completed(self, leads):
        self.is_searching = False
        self.extracted_leads = leads
        self.btn_search.config(state="normal", text="🔍 Start Lead Extraction")

        for idx, lead in enumerate(leads):
            self.tree.insert("", "end", values=(
                idx + 1,
                lead.get("name", "Lead"),
                f"+{lead.get('phone', '')}",
                lead.get("city", ""),
                lead.get("category", ""),
                lead.get("source", "Instagram")
            ))

        self.results_count_lbl.config(text=f"Discovered Leads: {len(leads)}")
        self.status_lbl.config(text=f"Extraction completed! {len(leads)} leads ready.", style="StatGreen.TLabel")

        if leads:
            self.btn_send_campaign.config(state="normal")
            self.btn_save_crm.config(state="normal")
            self.btn_export.config(state="normal")

    def transfer_to_campaign(self):
        if not self.extracted_leads:
            return

        if self.on_transfer_to_campaign:
            self.on_transfer_to_campaign(self.extracted_leads)
            self.top.destroy()
        else:
            messagebox.showinfo("Transfer Ready", f"Prepared {len(self.extracted_leads)} leads for campaign.")

    def save_to_crm(self):
        if not self.extracted_leads:
            return

        saved_count = 0
        for item in self.extracted_leads:
            ok, _ = add_or_update_contact(
                name=item.get("name", "Instagram Lead"),
                phone=item.get("phone", ""),
                city=item.get("city", ""),
                category=item.get("category", ""),
                status="Lead",
                tags="Instagram Lead,Cold Lead",
                notes=item.get("notes", "")
            )
            if ok:
                saved_count += 1

        messagebox.showinfo("CRM Sync Complete", f"Successfully saved {saved_count} leads into your CRM database!")

    def export_csv(self):
        if not self.extracted_leads:
            return

        fpath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"instagram_leads_{self.city_combo.get().lower()}_{self.niche_combo.get().lower().replace(' ', '_')}.csv"
        )
        if not fpath:
            return

        try:
            if pd:
                df = pd.DataFrame(self.extracted_leads)
                df.to_csv(fpath, index=False)
            else:
                import csv
                keys = self.extracted_leads[0].keys()
                with open(fpath, 'w', newline='', encoding='utf-8') as f:
                    dict_writer = csv.DictWriter(f, fieldnames=keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(self.extracted_leads)

            messagebox.showinfo("Export Successful", f"Saved {len(self.extracted_leads)} leads to:\n{os.path.basename(fpath)}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not save file: {str(e)}")
