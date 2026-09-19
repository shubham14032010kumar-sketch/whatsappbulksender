"""
AI Message Enhancer & Auto-Responder Management Dialog (ui/ai_assistant_dialog.py)
Interactive UI dialog allowing users to:
1. Generate high-converting Spintax templates with 1-click
2. Access Industry Sales Templates (Coaching, Real Estate, Retail, Services)
3. Configure 2-Way Auto-Responder Rules & Inbound Lead Triggers
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from core.ai_enhancer import INDUSTRY_TEMPLATES, generate_smart_spintax, get_template, list_industry_categories
from core.auto_responder import get_all_rules, add_rule, delete_rule, toggle_rule

class AIAssistantDialog:
    """Enterprise AI & Inbound Automation Hub."""

    def __init__(self, parent, on_insert_callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("🪄 Enterprise AI Message Enhancer & Auto-Responder Hub")
        self.top.geometry("740x580")
        self.top.configure(bg="#090d16")
        self.top.transient(parent)
        self.top.grab_set()

        self.on_insert = on_insert_callback

        # Header
        h_frame = ttk.Frame(self.top)
        h_frame.pack(fill="x", padx=20, pady=(15, 10))
        ttk.Label(h_frame, text="🪄 Enterprise AI & Inbound Sales Hub", style="Header.TLabel").pack(side="left")

        # Notebook
        self.nb = ttk.Notebook(self.top)
        self.nb.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.tab_ai = ttk.Frame(self.nb, style="TFrame")
        self.tab_auto = ttk.Frame(self.nb, style="TFrame")

        self.nb.add(self.tab_ai, text="🪄 AI Message Enhancer & Templates")
        self.nb.add(self.tab_auto, text="💬 2-Way Auto-Responder Rules")

        self.build_ai_tab()
        self.build_auto_responder_tab()

    # =========================================================================
    # TAB 1: AI MESSAGE ENHANCER & INDUSTRY TEMPLATES
    # =========================================================================
    def build_ai_tab(self):
        f = ttk.Frame(self.tab_ai, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        # Industry Presets Bar
        t_bar = ttk.Frame(f, style="Card.TFrame")
        t_bar.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(t_bar, text="Industry Presets:", style="CardTitle.TLabel").pack(side="left", padx=(0, 10))
        self.ind_combo = ttk.Combobox(t_bar, values=list_industry_categories(), state="readonly", width=28)
        self.ind_combo.set(list_industry_categories()[0])
        self.ind_combo.pack(side="left", padx=(0, 10))

        ttk.Button(t_bar, text="📥 Load Template", style="Secondary.TButton", command=self.load_industry_template).pack(side="left")

        # Prompt input label
        ttk.Label(f, text="Your Message / Offer Details (or customize below):", style="CardLabel.TLabel").pack(anchor="w", padx=10, pady=(10, 2))

        self.txt_content = scrolledtext.ScrolledText(f, height=12, bg="#050811", fg="#e5e7eb", font=("Consolas", 10), insertbackground="#38bdf8", relief="flat")
        self.txt_content.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Load initial template
        self.load_industry_template()

        # Action Buttons
        b_bar = ttk.Frame(f, style="Card.TFrame")
        b_bar.pack(fill="x", padx=10, pady=(10, 10))

        ttk.Button(b_bar, text="✨ Convert to Ban-Proof Spintax", style="Primary.TButton", command=self.convert_to_spintax).pack(side="left")
        ttk.Button(b_bar, text="📋 Insert into Campaign Composer", style="Success.TButton", command=self.insert_to_campaign).pack(side="right")

    def load_industry_template(self):
        cat = self.ind_combo.get()
        tpl = get_template(cat)
        if tpl:
            self.txt_content.delete("1.0", tk.END)
            self.txt_content.insert(tk.END, tpl)

    def convert_to_spintax(self):
        curr = self.txt_content.get("1.0", tk.END).strip()
        if not curr:
            messagebox.showwarning("Empty", "Please write a message first.")
            return
        spintax = generate_smart_spintax(curr)
        self.txt_content.delete("1.0", tk.END)
        self.txt_content.insert(tk.END, spintax)
        messagebox.showinfo("Success", "Message successfully transformed into multi-variant Spintax with dynamic personalizations!")

    def insert_to_campaign(self):
        content = self.txt_content.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Empty", "Message is empty.")
            return
        if self.on_insert:
            self.on_insert(content)
        messagebox.showinfo("Inserted", "Template successfully loaded into your Campaign Composer!")
        self.top.destroy()

    # =========================================================================
    # TAB 2: 2-WAY AUTO-RESPONDER RULES
    # =========================================================================
    def build_auto_responder_tab(self):
        f = ttk.Frame(self.tab_auto, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(f, text="24/7 Automated Inbound Rules (Auto-reply & Lead Tagging):", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 5))

        # Rules TreeView
        cols = ("id", "keyword", "match", "tag", "reply")
        self.tree = ttk.Treeview(f, columns=cols, show="headings", height=7, selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("keyword", text="Trigger Keywords")
        self.tree.heading("match", text="Match")
        self.tree.heading("tag", text="Lead Tag")
        self.tree.heading("reply", text="Automated Reply Preview")

        self.tree.column("id", width=35, anchor="center")
        self.tree.column("keyword", width=180)
        self.tree.column("match", width=70, anchor="center")
        self.tree.column("tag", width=110, anchor="center")
        self.tree.column("reply", width=260)

        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.refresh_rules()

        # Add New Rule Section
        add_card = ttk.Frame(f, style="Card.TFrame")
        add_card.pack(fill="x", padx=10, pady=(10, 5))

        row1 = ttk.Frame(add_card, style="Card.TFrame")
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Keywords (comma-separated):", style="CardLabel.TLabel").pack(side="left")
        self.ent_kw = ttk.Entry(row1, width=32)
        self.ent_kw.pack(side="left", padx=5)

        ttk.Label(row1, text="Lead Tag:", style="CardLabel.TLabel").pack(side="left", padx=(10, 0))
        self.tag_combo = ttk.Combobox(row1, values=["HOT_LEAD", "WARM_LEAD", "DEMO_REQUEST", "LOCATION_INQUIRY"], state="readonly", width=14)
        self.tag_combo.set("HOT_LEAD")
        self.tag_combo.pack(side="left", padx=5)

        row2 = ttk.Frame(add_card, style="Card.TFrame")
        row2.pack(fill="x", pady=4)
        ttk.Label(row2, text="Auto-Reply Text:", style="CardLabel.TLabel").pack(side="left")
        self.ent_reply = ttk.Entry(row2, width=60)
        self.ent_reply.pack(side="left", padx=5, fill="x", expand=True)

        btn_row = ttk.Frame(add_card, style="Card.TFrame")
        btn_row.pack(fill="x", pady=(5, 0))
        ttk.Button(btn_row, text="➕ Add Rule", style="Primary.TButton", command=self.add_new_rule).pack(side="left")
        ttk.Button(btn_row, text="🗑️ Delete Selected", style="Secondary.TButton", command=self.delete_selected_rule).pack(side="left", padx=10)

    def refresh_rules(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        rules = get_all_rules()
        for r in rules:
            self.tree.insert("", tk.END, values=(r["id"], r["keyword"], r.get("match_type", "CONTAINS"), r.get("tag_lead", "LEAD"), r.get("reply_text", "")[:45] + "..."))

    def add_new_rule(self):
        kw = self.ent_kw.get().strip()
        reply = self.ent_reply.get().strip()
        tag = self.tag_combo.get()
        if not kw or not reply:
            messagebox.showwarning("Incomplete", "Keywords and Reply text are required.")
            return
        add_rule(kw, reply, tag_lead=tag)
        self.ent_kw.delete(0, tk.END)
        self.ent_reply.delete(0, tk.END)
        self.refresh_rules()
        messagebox.showinfo("Success", f"Auto-reply rule added for keywords: '{kw}'")

    def delete_selected_rule(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a rule to delete.")
            return
        val = self.tree.item(sel[0], "values")
        rule_id = val[0]
        delete_rule(rule_id)
        self.refresh_rules()
