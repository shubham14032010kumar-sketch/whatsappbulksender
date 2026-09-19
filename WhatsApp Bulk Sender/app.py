"""
WhatsApp Bulk Campaign Sender — Enterprise Master Platform (app.py)
Unified desktop application orchestrator coordinating:
- Phase 1: CRM, Groups, Tags, Segmentation, Visual Builder, Analytics
- Phase 2: User Authentication, Team Roles (RBAC), Licensing, Admin Panel
- Phase 3: REST API Server, Audit Logging, Backup & Restore
- Phase 4: Onboarding Wizard, Comprehensive Settings Hub, Multi-Provider Architecture
"""

import os
import sys
import time
import random
import threading
import queue
import re
from datetime import datetime
import tkinter as 
from tkinter import ttk, filedialog, messagebox, scrolledtext

# Core Architecture Modules
from core.db import init_database, get_connection
from core.auth import SessionManager, authenticate_user
from core.licensing import get_active_license, get_machine_id, activate_key, deactivate_license
from core.crm import filter_contacts, bulk_import_contacts, add_or_update_contact
from core.campaign_engine import create_campaign, get_all_campaigns, update_campaign_status, parse_spintax
from core.audit import log_audit
from core.whatsapp.selenium_driver import SeleniumChromeProvider
from core.whatsapp.cloud_api import MetaCloudApiProvider
from api.server import start_api_server

# UI Components
from ui.theme import apply_theme, BG_DARK, BG_CARD, BG_LIGHT, TEXT_LIGHT, TEXT_MUTED, ACCENT_GREEN, ACCENT_BLUE, ACCENT_RED, ACCENT_AMBER
from ui.onboarding import OnboardingWizardDialog
from ui.auth_dialog import AuthLoginDialog
from ui.crm_view import CrmWorkspaceFrame
from ui.analytics_view import AnalyticsDashboardFrame
from ui.admin_view import AdminPanelFrame
from ui.settings_view import SettingsDialog
from ui.campaign_wizard import VisualCampaignWizardDialog
from ui.ai_assistant_dialog import AIAssistantDialog
from ui.lead_extractor_dialog import InstagramLeadExtractorDialog
from ui.quick_paste_dialog import DirectPasteNumbersDialog
from core.auto_responder import init_auto_responder_table

try:
    import pandas as pd
except ImportError:
    pd = None


class WhatsAppEnterpriseApp:
    """Enterprise Master Application Coordinator."""

    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Bulk Campaign Sender — Enterprise Commercial Platform")
        self.root.geometry("1240x860")
        self.root.minsize(1080, 720)

        # Initialize Enterprise Database schema
        init_database()

        # Start Local REST API in background
        self.api_server = start_api_server(port=8000)

        # State Variables
        self.contact_df = None
        self.file_path = None
        self.attachment_path = None
        self.detected_columns = ["Name", "Phone", "City", "Company", "Category"]
        self.phone_column = "Phone"
        self.name_column = "Name"

        self.campaign_running = False
        self.campaign_paused = False
        self.stop_requested = False
        self.current_campaign_id = None
        self.campaign_results = []

        self.license_info = get_active_license()
        self.schedule_enabled_var = tk.BooleanVar(value=False)
        self.log_queue = queue.Queue()
        self.provider = None
        self.campaign_thread = None

        # Check if running in Client Edition mode
        self.is_client_mode = os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_mode.flag")) or (os.environ.get("CLIENT_EDITION") == "1")

        # Authenticate session
        if not SessionManager.is_authenticated():
            if self.is_client_mode:
                SessionManager.set_user({"name": "Client", "role": "Staff", "id": 999})
            else:
                u, _ = authenticate_user("admin@enterprise.local", "admin123")
                if u:
                    SessionManager.set_user(u)

        # Apply Modern Dark Theme
        self.style = apply_theme(self.root)

        # Build UI Structure
        self.build_ui()
        self.root.after(100, self.process_queue)
        self.root.after(800, self.check_first_launch_onboarding)

    def check_first_launch_onboarding(self):
        """Checks if first-launch onboarding should be displayed."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'onboarding_completed'")
            row = cursor.fetchone()
            if not row:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT OR REPLACE INTO settings (key, value, category, updated_at) VALUES ('onboarding_completed', '1', 'general', ?)", (now,))
                conn.commit()
                OnboardingWizardDialog(self.root)

    def build_ui(self):
        # 1. Header Bar
        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill="x", padx=20, pady=10)

        left_h = ttk.Frame(header, style="TFrame")
        left_h.pack(side="left")

        ttk.Label(left_h, text="⚡ SHAKTIX", style="Header.TLabel").pack(side="left")
        ttk.Label(left_h, text="● ENTERPRISE SUITE ACTIVE", style="SubHeader.TLabel").pack(side="left", padx=15)

        # Quick Wizard Button & AI Hub in Header
        ttk.Button(left_h, text="⚡ Visual Campaign Wizard", style="ActionBlue.TButton", command=self.open_campaign_wizard).pack(side="left", padx=(10, 4))
        ttk.Button(left_h, text="🪄 AI Enhancer & Inbound Hub", style="Primary.TButton", command=self.open_ai_assistant).pack(side="left", padx=4)
        ttk.Button(left_h, text="🎯 Lead Finder", style="Secondary.TButton", command=self.open_lead_extractor).pack(side="left", padx=4)

        # Right Header: User Profile + License Badge + Settings Button
        right_h = ttk.Frame(header, style="TFrame")
        right_h.pack(side="right")

        user = SessionManager.get_user() or {"name": "Admin", "role": "Owner"}
        self.user_lbl = ttk.Label(right_h, text=f"👤 {user.get('name')} ({user.get('role')})", style="CardLabel.TLabel")
        self.user_lbl.pack(side="left", padx=8)

        self.license_badge_lbl = ttk.Label(right_h, text="", style="LicenseTrial.TLabel")
        self.license_badge_lbl.pack(side="left", padx=8)
        self.update_header_license_badge()

        ttk.Button(right_h, text="⚙️ Settings", style="Secondary.TButton", command=lambda: SettingsDialog(self.root)).pack(side="left", padx=3)
        ttk.Button(right_h, text="👋 Tour", style="Secondary.TButton", command=lambda: OnboardingWizardDialog(self.root)).pack(side="left", padx=3)

        # 2. Main Navigation Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Tabs
        self.tab_campaign = ttk.Frame(self.notebook, style="TFrame")
        self.tab_crm = ttk.Frame(self.notebook, style="TFrame")
        self.tab_analytics = ttk.Frame(self.notebook, style="TFrame")
        self.tab_templates = ttk.Frame(self.notebook, style="TFrame")
        self.tab_blacklist = ttk.Frame(self.notebook, style="TFrame")
        self.tab_license = ttk.Frame(self.notebook, style="TFrame")
        self.tab_admin = ttk.Frame(self.notebook, style="TFrame")

        self.notebook.add(self.tab_campaign, text="🚀 Campaign Sender")
        self.notebook.add(self.tab_crm, text="📇 CRM & Audience")
        self.notebook.add(self.tab_analytics, text="📈 Analytics & Reports")
        self.notebook.add(self.tab_templates, text="✍️ Message Templates")
        self.notebook.add(self.tab_blacklist, text="🚫 Blacklist Manager")
        self.notebook.add(self.tab_license, text="🔑 License & Plans")

        # Admin tab only for Owner / Admin (strictly hidden in Client Edition)
        if not self.is_client_mode and SessionManager.has_permission("users"):
            self.notebook.add(self.tab_admin, text="⚙️ Super Admin")
            self.admin_view = AdminPanelFrame(self.tab_admin)
        else:
            self.admin_view = None

        # Build Sub-views
        self.build_campaign_tab()
        self.crm_view = CrmWorkspaceFrame(self.tab_crm, on_transfer_to_campaign=self.handle_crm_audience_transfer)
        self.analytics_view = AnalyticsDashboardFrame(self.tab_analytics)
        self.build_templates_tab()
        self.build_blacklist_tab()
        self.build_license_tab()

    def update_header_license_badge(self):
        self.license_info = get_active_license()
        st = self.license_info.get("status")
        plan = self.license_info.get("plan", "Starter")
        days = self.license_info.get("days_remaining", 0)

        if st == "ACTIVE":
            self.license_badge_lbl.config(
                text=f"🟢 {plan} LICENSE ({days} Days)",
                style="LicenseActive.TLabel"
            )
        elif st == "EXPIRED":
            self.license_badge_lbl.config(
                text="🔴 LICENSE EXPIRED",
                style="LicenseExpired.TLabel"
            )
        else:
            self.license_badge_lbl.config(
                text="🟡 FREE TRIAL (15 Msgs Limit)",
                style="LicenseTrial.TLabel"
            )

    # =========================================================================
    # TAB 1: CAMPAIGN SENDER WORKSPACE
    # =========================================================================
    def build_campaign_tab(self):
        main_c = ttk.Frame(self.tab_campaign, style="TFrame")
        main_c.pack(fill="both", expand=True, pady=10)

        left_col = ttk.Frame(main_c, style="TFrame")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_col = ttk.Frame(main_c, style="TFrame")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Card 1: Contact File & Audience
        file_card = ttk.Frame(left_col, style="Card.TFrame")
        file_card.pack(fill="x", pady=(0, 10), ipady=8, ipadx=10)

        ttk.Label(file_card, text="1. Audience Source & Column Mapping", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 5))

        f_bar = ttk.Frame(file_card, style="Card.TFrame")
        f_bar.pack(fill="x", padx=10)

        self.browse_btn = ttk.Button(f_bar, text="📁 Browse Excel/CSV", style="Secondary.TButton", command=self.browse_file)
        self.browse_btn.pack(side="left")

        self.paste_btn = ttk.Button(f_bar, text="📋 Paste Numbers", style="ActionBlue.TButton", command=self.open_paste_dialog)
        self.paste_btn.pack(side="left", padx=4)

        self.lead_btn = ttk.Button(f_bar, text="🎯 Extract Leads", style="Primary.TButton", command=self.open_lead_extractor)
        self.lead_btn.pack(side="left", padx=4)

        self.crm_pick_btn = ttk.Button(f_bar, text="📇 CRM Segment", style="Secondary.TButton", command=lambda: self.notebook.select(self.tab_crm))
        self.crm_pick_btn.pack(side="left", padx=4)

        self.file_status_lbl = ttk.Label(f_bar, text="No contacts loaded", style="CardLabel.TLabel")
        self.file_status_lbl.pack(side="left", padx=8)

        # Mapping Row
        m_row = ttk.Frame(file_card, style="Card.TFrame")
        m_row.pack(fill="x", padx=10, pady=(8, 0))

        ttk.Label(m_row, text="Phone Column:", style="CardLabel.TLabel").grid(row=0, column=0, sticky="w", pady=2)
        self.phone_col_combo = ttk.Combobox(m_row, state="readonly", width=16)
        self.phone_col_combo.grid(row=0, column=1, sticky="w", padx=(4, 15), pady=2)

        ttk.Label(m_row, text="Name Column:", style="CardLabel.TLabel").grid(row=0, column=2, sticky="w", pady=2)
        self.name_col_combo = ttk.Combobox(m_row, state="readonly", width=16)
        self.name_col_combo.grid(row=0, column=3, sticky="w", padx=4, pady=2)

        # Sanitizer Row
        s_row = ttk.Frame(file_card, style="Card.TFrame")
        s_row.pack(fill="x", padx=10, pady=(6, 2))

        self.add_cc_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(s_row, text="Auto Prepend Country Code:", variable=self.add_cc_var).pack(side="left")
        self.cc_entry = ttk.Entry(s_row, width=5)
        self.cc_entry.insert(0, "91")
        self.cc_entry.pack(side="left", padx=4)

        self.dedup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(s_row, text="Deduplicate", variable=self.dedup_var).pack(side="left", padx=12)

        # Card 2: Message Template & Media
        msg_card = ttk.Frame(left_col, style="Card.TFrame")
        msg_card.pack(fill="both", expand=True, pady=(0, 10), ipady=8, ipadx=10)

        m_top_bar = ttk.Frame(msg_card, style="Card.TFrame")
        m_top_bar.pack(fill="x", padx=10, pady=(5, 5))
        ttk.Label(m_top_bar, text="2. Message Template & Attachments", style="CardTitle.TLabel").pack(side="left")
        ttk.Button(m_top_bar, text="🪄 AI Magic Spintax", style="Secondary.TButton", command=self.open_ai_assistant).pack(side="right")

        # Dynamic Tags Row
        self.tags_frame = ttk.Frame(msg_card, style="Card.TFrame")
        self.tags_frame.pack(fill="x", padx=10, pady=(0, 4))
        self.render_tags_bar()

        # Formatting & Emojis Bar
        fmt_frame = ttk.Frame(msg_card, style="Card.TFrame")
        fmt_frame.pack(fill="x", padx=10, pady=(2, 6))

        for fmt in ["*Bold*", "_Italic_", "~Strike~", "```Code```"]:
            char = fmt.replace("Bold", "").replace("Italic", "").replace("Strike", "").replace("Code", "")
            ttk.Button(fmt_frame, text=fmt, style="Secondary.TButton", command=lambda c=char: self.msg_box.insert(tk.INSERT, c)).pack(side="left", padx=2)

        for em in ["😀", "👍", "🔥", "✅", "🎉", "📞", "💼", "📦", "📢"]:
            ttk.Button(fmt_frame, text=em, width=3, style="Secondary.TButton", command=lambda e=em: self.msg_box.insert(tk.INSERT, e)).pack(side="left", padx=1)

        self.msg_box = scrolledtext.ScrolledText(msg_card, height=8, bg="#090d16", fg=TEXT_LIGHT, insertbackground="#fff", font=("Segoe UI", 10))
        self.msg_box.pack(fill="both", expand=True, padx=10, pady=5)
        self.msg_box.insert(tk.END, "Hello {Name},\n\nWe are pleased to connect with you. Please find our exclusive updates.\n\nBest Regards,\nTeam")

        att_row = ttk.Frame(msg_card, style="Card.TFrame")
        att_row.pack(fill="x", padx=10, pady=(4, 2))
        ttk.Button(att_row, text="📎 Attach Media", style="Secondary.TButton", command=self.browse_attachment).pack(side="left")
        ttk.Button(att_row, text="Clear", style="Secondary.TButton", command=self.clear_attachment).pack(side="left", padx=4)
        self.attach_lbl = ttk.Label(att_row, text="None selected", style="CardLabel.TLabel")
        self.attach_lbl.pack(side="left", padx=8)

        # Card 3: Anti-Ban & Execution Engine
        settings_card = ttk.Frame(right_col, style="Card.TFrame")
        settings_card.pack(fill="x", pady=(0, 10), ipady=8, ipadx=10)

        ttk.Label(settings_card, text="3. Anti-Ban Engine & Speed Throttling", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 5))

        preset_row = ttk.Frame(settings_card, style="Card.TFrame")
        preset_row.pack(fill="x", padx=10, pady=(2, 4))
        ttk.Label(preset_row, text="Speed Presets:", style="CardLabel.TLabel").pack(side="left")
        ttk.Button(preset_row, text="🛡️ Safe (10-18s)", style="Secondary.TButton", command=lambda: self.set_delay_preset(10, 18)).pack(side="left", padx=2)
        ttk.Button(preset_row, text="⚡ Balanced (6-12s)", style="Secondary.TButton", command=lambda: self.set_delay_preset(6, 12)).pack(side="left", padx=2)
        ttk.Button(preset_row, text="🚀 Turbo (3-6s)", style="Secondary.TButton", command=lambda: self.set_delay_preset(3, 6)).pack(side="left", padx=2)

        d_row = ttk.Frame(settings_card, style="Card.TFrame")
        d_row.pack(fill="x", padx=10, pady=4)

        ttk.Label(d_row, text="Random Pause:", style="CardLabel.TLabel").pack(side="left")
        self.min_delay_entry = ttk.Entry(d_row, width=4)
        self.min_delay_entry.insert(0, "8")
        self.min_delay_entry.pack(side="left", padx=4)
        ttk.Label(d_row, text="to", style="CardLabel.TLabel").pack(side="left")
        self.max_delay_entry = ttk.Entry(d_row, width=4)
        self.max_delay_entry.insert(0, "15")
        self.max_delay_entry.pack(side="left", padx=4)
        ttk.Label(d_row, text="sec", style="CardLabel.TLabel").pack(side="left", padx=(0, 10))

        self.typing_sim_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(d_row, text="Typing Simulator", variable=self.typing_sim_var).pack(side="left", padx=10)

        # Schedule Row
        sched_row = ttk.Frame(settings_card, style="Card.TFrame")
        sched_row.pack(fill="x", padx=10, pady=4)
        self.sched_chk = ttk.Checkbutton(sched_row, text="⏱️ Scheduled Launch (24hr HH:MM):", variable=self.schedule_enabled_var)
        self.sched_chk.pack(side="left")
        self.sched_time_ent = ttk.Entry(sched_row, width=7)
        self.sched_time_ent.insert(0, "14:30")
        self.sched_time_ent.pack(side="left", padx=6)

        # Action Buttons
        btn_bar = ttk.Frame(settings_card, style="Card.TFrame")
        btn_bar.pack(fill="x", padx=10, pady=(10, 4))

        self.start_btn = ttk.Button(btn_bar, text="▶ START CAMPAIGN", style="Primary.TButton", command=self.start_campaign)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.pause_btn = ttk.Button(btn_bar, text="⏸ PAUSE", style="Warning.TButton", command=self.toggle_pause, state="disabled")
        self.pause_btn.pack(side="left", padx=3)

        self.stop_btn = ttk.Button(btn_bar, text="⏹ STOP", style="Danger.TButton", command=self.stop_campaign, state="disabled")
        self.stop_btn.pack(side="left", padx=(3, 0))

        # Progress
        prog_frame = ttk.Frame(settings_card, style="Card.TFrame")
        prog_frame.pack(fill="x", padx=10, pady=(6, 2))
        self.progress = ttk.Progressbar(prog_frame, style="Green.Horizontal.TProgressbar", mode="determinate")
        self.progress.pack(fill="x")
        self.progress_lbl = ttk.Label(prog_frame, text="Engine Idle — Ready", style="CardLabel.TLabel")
        self.progress_lbl.pack(anchor="w", pady=(2, 0))

        # Card 4: Real-time Badges & Console
        stats_card = ttk.Frame(right_col, style="Card.TFrame")
        stats_card.pack(fill="both", expand=True, pady=(0, 10), ipady=8, ipadx=10)

        badges_f = ttk.Frame(stats_card, style="Card.TFrame")
        badges_f.pack(fill="x", padx=10, pady=4)

        self.lbl_stat_total = ttk.Label(badges_f, text="Total: 0", style="StatBlue.TLabel")
        self.lbl_stat_total.pack(side="left", expand=True, fill="x", padx=2)

        self.lbl_stat_sent = ttk.Label(badges_f, text="Sent: 0", style="StatGreen.TLabel")
        self.lbl_stat_sent.pack(side="left", expand=True, fill="x", padx=2)

        self.lbl_stat_failed = ttk.Label(badges_f, text="Failed: 0", style="StatRed.TLabel")
        self.lbl_stat_failed.pack(side="left", expand=True, fill="x", padx=2)

        self.lbl_stat_pending = ttk.Label(badges_f, text="Pending: 0", style="StatYellow.TLabel")
        self.lbl_stat_pending.pack(side="left", expand=True, fill="x", padx=2)

        l_hdr = ttk.Frame(stats_card, style="Card.TFrame")
        l_hdr.pack(fill="x", padx=10, pady=(4, 2))
        ttk.Label(l_hdr, text="Live Engine Console & Logs", style="CardTitle.TLabel").pack(side="left")

        self.log_box = scrolledtext.ScrolledText(stats_card, height=9, bg="#050811", fg="#e5e7eb", font=("Consolas", 9), relief="flat")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=4)
        self.log_box.tag_config("SUCCESS", foreground="#34d399")
        self.log_box.tag_config("ERROR", foreground="#f87171")
        self.log_box.tag_config("WARNING", foreground="#fbbf24")
        self.log_box.tag_config("INFO", foreground="#60a5fa")

        self.append_log("Enterprise Platform Engine initialized. Select Audience or launch Visual Wizard.", "INFO")

    def render_tags_bar(self):
        for w in self.tags_frame.winfo_children():
            w.destroy()
        ttk.Label(self.tags_frame, text="Variables:", style="CardLabel.TLabel").pack(side="left", padx=(0, 5))
        for col in self.detected_columns:
            btn = ttk.Button(self.tags_frame, text=f"{{{col}}}", style="Secondary.TButton", command=lambda c=col: self.msg_box.insert(tk.INSERT, f"{{{c}}}"))
            btn.pack(side="left", padx=2)

    def open_ai_assistant(self):
        AIAssistantDialog(self.root, on_insert_callback=self.handle_ai_insert)

    def handle_ai_insert(self, template_text):
        self.msg_box.delete("1.0", tk.END)
        self.msg_box.insert(tk.END, template_text)
        self.append_log("Loaded AI Enhanced Spintax into Message Composer.", "SUCCESS")

    def open_campaign_wizard(self):
        contacts = []
        if self.contact_df is not None and not self.contact_df.empty:
            contacts = self.contact_df.to_dict(orient="records")
        VisualCampaignWizardDialog(self.root, preloaded_contacts=contacts, on_launch_callback=self.handle_wizard_launch)

    def handle_wizard_launch(self, camp_data):
        self.msg_box.delete("1.0", tk.END)
        self.msg_box.insert(tk.END, camp_data["template"])
        self.min_delay_entry.delete(0, tk.END)
        self.min_delay_entry.insert(0, str(camp_data["min_delay"]))
        self.max_delay_entry.delete(0, tk.END)
        self.max_delay_entry.insert(0, str(camp_data["max_delay"]))
        self.attachment_path = camp_data.get("attachment")
        self.attach_lbl.config(text=self.attachment_path or "None selected")

        if camp_data.get("scheduled_at"):
            self.schedule_enabled_var.set(True)
            self.sched_time_ent.delete(0, tk.END)
            self.sched_time_ent.insert(0, camp_data["scheduled_at"])

        self.start_campaign()

    def handle_crm_audience_transfer(self, filtered_contacts):
        df = pd.DataFrame(filtered_contacts)
        self.contact_df = df
        self.detected_columns = list(df.columns)
        self.phone_column = "phone" if "phone" in df.columns else self.detected_columns[0]
        self.name_column = "name" if "name" in df.columns else self.detected_columns[0]

        self.phone_col_combo['values'] = self.detected_columns
        self.phone_col_combo.set(self.phone_column)
        self.name_col_combo['values'] = self.detected_columns
        self.name_col_combo.set(self.name_column)

        self.file_status_lbl.config(text=f"Loaded from CRM: {len(df)} Contacts")
        self.update_stat_badges(len(df), 0, 0, len(df))
        self.render_tags_bar()

        self.notebook.select(self.tab_campaign)
        self.append_log(f"Transferred {len(df)} audience contacts from CRM into Campaign Queue.", "SUCCESS")
        messagebox.showinfo("Audience Loaded", f"Transferred {len(df)} contacts into Campaign Sender!\nClick Start or launch the Visual Wizard.")

    def set_delay_preset(self, min_s, max_s):
        self.min_delay_entry.delete(0, tk.END)
        self.min_delay_entry.insert(0, str(min_s))
        self.max_delay_entry.delete(0, tk.END)
        self.max_delay_entry.insert(0, str(max_s))
        self.typing_sim_var.set(True)
        self.append_log(f"Applied speed preset: {min_s}s - {max_s}s with Typing Simulator.", "INFO")

    def open_paste_dialog(self):
        DirectPasteNumbersDialog(self.root, on_load_callback=self.handle_raw_paste_load)

    def handle_raw_paste_load(self, df, count):
        self.contact_df = df
        self.detected_columns = list(df.columns)
        self.phone_column = "Phone"
        self.name_column = "Name"

        self.phone_col_combo['values'] = self.detected_columns
        self.phone_col_combo.set(self.phone_column)
        self.name_col_combo['values'] = self.detected_columns
        self.name_col_combo.set(self.name_column)

        self.file_status_lbl.config(text=f"Loaded from Paste: {count} Numbers")
        self.update_stat_badges(count, 0, 0, count)
        self.render_tags_bar()
        self.append_log(f"Loaded {count} raw numbers directly into Campaign Queue.", "SUCCESS")
        messagebox.showinfo("Numbers Loaded", f"Successfully loaded {count} numbers!\nNo Excel needed. Write your message and click Start.")

    def open_lead_extractor(self):
        InstagramLeadExtractorDialog(self.root, on_transfer_to_campaign=self.handle_lead_extractor_transfer)

    def handle_lead_extractor_transfer(self, leads):
        if not leads:
            return
        df = pd.DataFrame(leads) if pd else None
        if df is None:
            return
        self.contact_df = df
        self.detected_columns = list(df.columns)
        self.phone_column = "phone" if "phone" in df.columns else self.detected_columns[0]
        self.name_column = "name" if "name" in df.columns else self.detected_columns[0]

        self.phone_col_combo['values'] = self.detected_columns
        self.phone_col_combo.set(self.phone_column)
        self.name_col_combo['values'] = self.detected_columns
        self.name_col_combo.set(self.name_column)

        self.file_status_lbl.config(text=f"Loaded from Lead Finder: {len(df)} Leads")
        self.update_stat_badges(len(df), 0, 0, len(df))
        self.render_tags_bar()
        self.notebook.select(self.tab_campaign)
        self.append_log(f"Transferred {len(df)} extracted leads into Campaign Queue.", "SUCCESS")
        messagebox.showinfo("Leads Loaded", f"Loaded {len(df)} targeted leads into Campaign Sender!\nClick START to begin broadcasting.")

    def browse_file(self):
        if not pd:
            messagebox.showerror("Pandas Required", "Pandas is required to read Excel/CSV files.")
            return

        f = filedialog.askopenfilename(
            title="Select Contacts File",
            filetypes=[("Excel & CSV Files", "*.xlsx *.xls *.csv *.txt"), ("Excel", "*.xlsx *.xls"), ("CSV", "*.csv")]
        )
        if not f:
            return

        try:
            if f.endswith(".csv"):
                df = pd.read_csv(f, dtype=str)
            elif f.endswith(".txt"):
                lines = [line.strip() for line in open(f, 'r', encoding='utf-8') if line.strip()]
                df = pd.DataFrame({"Phone": lines, "Name": ["Customer"] * len(lines)})
            else:
                df = pd.read_excel(f, dtype=str)

            if df.empty:
                messagebox.showwarning("Empty File", "File contains no rows.")
                return

            self.file_path = f
            self.contact_df = df
            self.detected_columns = list(df.columns)
            self.phone_column = next((c for c in self.detected_columns if any(k in c.lower() for k in ["phone", "mobile", "contact", "number", "whatsapp"])), self.detected_columns[0])
            self.name_column = next((c for c in self.detected_columns if any(k in c.lower() for k in ["name", "customer", "person"])), self.detected_columns[0])

            self.phone_col_combo['values'] = self.detected_columns
            self.phone_col_combo.set(self.phone_column)
            self.name_col_combo['values'] = self.detected_columns
            self.name_col_combo.set(self.name_column)

            base = os.path.basename(f)
            self.file_status_lbl.config(text=f"Loaded: {base} ({len(df)} contacts)")
            self.update_stat_badges(len(df), 0, 0, len(df))
            self.render_tags_bar()
            self.append_log(f"Loaded '{base}' with {len(df)} contacts.", "SUCCESS")

        except Exception as e:
            messagebox.showerror("File Error", f"Failed: {str(e)}")

    def browse_attachment(self):
        p = filedialog.askopenfilename(
            title="Select Attachment",
            filetypes=[("All Media", "*.jpg *.jpeg *.png *.webp *.pdf *.docx *.xlsx *.mp4")]
        )
        if p:
            self.attachment_path = p
            self.attach_lbl.config(text=os.path.basename(p))

    def clear_attachment(self):
        self.attachment_path = None
        self.attach_lbl.config(text="None selected")

    def update_stat_badges(self, total, sent, failed, pending):
        self.lbl_stat_total.config(text=f"Total: {total}")
        self.lbl_stat_sent.config(text=f"Sent: {sent}")
        self.lbl_stat_failed.config(text=f"Failed: {failed}")
        self.lbl_stat_pending.config(text=f"Pending: {pending}")

    def start_campaign(self):
        if self.campaign_running:
            return

        if self.contact_df is None or self.contact_df.empty:
            messagebox.showwarning("No Contacts", "Please load contacts from file or CRM first.")
            return

        msg_template = self.msg_box.get("1.0", tk.END).strip()
        if not msg_template and not self.attachment_path:
            messagebox.showwarning("Empty Message", "Please write a message template or select media.")
            return

        # Check License Entitlements
        self.license_info = get_active_license()
        max_limit = self.license_info.get("limits", {}).get("max_contacts", 500)
        if self.license_info.get("status") != "ACTIVE":
            max_limit = 15  # Free Trial hard cap

        if len(self.contact_df) > max_limit:
            res = messagebox.askyesno(
                "Plan Volume Limit",
                f"Your current license ({self.license_info.get('plan')}) allows {max_limit} messages per run.\n"
                f"Your list has {len(self.contact_df)} contacts.\n\n"
                f"Send to first {max_limit} contacts only?\n(Click 'No' to upgrade/activate key)."
            )
            if not res:
                self.notebook.select(self.tab_license)
                return
            self.contact_df = self.contact_df.head(max_limit)

        try:
            min_d = int(self.min_delay_entry.get().strip())
            max_d = int(self.max_delay_entry.get().strip())
            if min_d < 1 or max_d < min_d:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Invalid Delays", "Delays must be positive integers.")
            return

        sched_time = ""
        if self.schedule_enabled_var.get():
            sched_time = self.sched_time_ent.get().strip()
            try:
                datetime.strptime(sched_time, "%H:%M")
            except ValueError:
                messagebox.showerror("Invalid Schedule", "Schedule time must be 24hr HH:MM.")
                return

        c_name = f"Campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        recipients_list = self.contact_df.to_dict(orient="records")
        self.current_campaign_id = create_campaign(c_name, scheduled_at=sched_time, min_delay=min_d, max_delay=max_d, recipient_list=recipients_list)
        self.campaign_results = []

        self.campaign_running = True
        self.campaign_paused = False
        self.stop_requested = False

        self.start_btn.config(state="disabled")
        self.browse_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="⏸ PAUSE")
        self.stop_btn.config(state="normal")

        self.progress["value"] = 0
        self.progress["maximum"] = len(self.contact_df)

        cc = self.cc_entry.get().strip() if self.add_cc_var.get() else ""
        sim_typing = self.typing_sim_var.get()

        self.campaign_thread = threading.Thread(
            target=self.run_campaign_worker,
            args=(msg_template, min_d, max_d, cc, sim_typing, sched_time),
            daemon=True
        )
        self.campaign_thread.start()

    def toggle_pause(self):
        if not self.campaign_running:
            return
        self.campaign_paused = not self.campaign_paused
        if self.provider:
            self.provider.is_paused = self.campaign_paused
        if self.campaign_paused:
            self.pause_btn.config(text="▶ RESUME")
            self.append_log("Campaign PAUSED by user.", "WARNING")
            update_campaign_status(self.current_campaign_id, "Paused")
        else:
            self.pause_btn.config(text="⏸ PAUSE")
            self.append_log("Campaign RESUMED by user.", "INFO")
            update_campaign_status(self.current_campaign_id, "Running")

    def stop_campaign(self):
        if not self.campaign_running:
            return
        if messagebox.askyesno("Stop Campaign", "Stop transmission?"):
            self.stop_requested = True
            if self.provider:
                self.provider.is_stopped = True
            self.append_log("Stop requested by user...", "WARNING")
            update_campaign_status(self.current_campaign_id, "Failed")

    def run_campaign_worker(self, msg_template, min_d, max_d, country_code, sim_typing, sched_time):
        if sched_time:
            self.log_queue.put(("LOG", (f"⏱️ Scheduled for {sched_time}. Waiting for target time...", "WARNING")))
            while not self.stop_requested:
                if datetime.now().strftime("%H:%M") >= sched_time:
                    self.log_queue.put(("LOG", (f"⏱️ Scheduled time {sched_time} reached! Commencing transmission...", "SUCCESS")))
                    break
                time.sleep(5)
            if self.stop_requested:
                self.finish_campaign("Scheduled run cancelled.")
                return

        update_campaign_status(self.current_campaign_id, "Running")
        
        # Determine Provider (Selenium Browser vs Meta Cloud API)
        provider_type = "SELENIUM"
        meta_phone_id = ""
        meta_token = ""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key, value FROM settings WHERE key IN ('active_provider', 'meta_phone_id', 'meta_access_token')")
                for k, v in cursor.fetchall():
                    if k == 'active_provider' and v:
                        provider_type = str(v).upper()
                    elif k == 'meta_phone_id':
                        meta_phone_id = str(v or "").strip()
                    elif k == 'meta_access_token':
                        meta_token = str(v or "").strip()
        except Exception:
            pass

        if provider_type == "META_CLOUD" and meta_phone_id and meta_token:
            self.log_queue.put(("LOG", ("Initializing Official Meta Cloud API Provider...", "INFO")))
            self.provider = MetaCloudApiProvider(meta_phone_id, meta_token, log_callback=lambda m, l: self.log_queue.put(("LOG", (m, l))))
            if not self.provider.initialize():
                self.finish_campaign("Meta Cloud API initialization failed. Check credentials.")
                return
        else:
            self.log_queue.put(("LOG", ("Initializing WhatsApp Chrome Engine with Anti-Bot Shields...", "INFO")))
            self.provider = SeleniumChromeProvider(log_callback=lambda m, l: self.log_queue.put(("LOG", (m, l))))
            if not self.provider.initialize() or not self.provider.wait_for_login(timeout=120):
                self.finish_campaign("Provider initialization or login failed.")
                return

        total = len(self.contact_df)
        sent_cnt = 0
        failed_cnt = 0
        processed_phones = set()

        # Fetch SQLite Blacklist set
        blacklisted = set()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT phone FROM blacklist")
            blacklisted = {r[0] for r in cursor.fetchall()}

        for idx, row in self.contact_df.iterrows():
            if self.stop_requested:
                break
            while self.campaign_paused and not self.stop_requested:
                time.sleep(1)

            raw_ph = row.get(self.phone_column, "")
            ph = re.sub(r"[^\d+]", "", str(raw_ph or "").strip())
            if ph.startswith("+"):
                ph = ph[1:]
            if country_code and len(ph) == 10 and not ph.startswith(country_code):
                ph = f"{country_code}{ph}"

            # Smart Fallback Name Logic for Raw Numbers
            raw_name = str(row.get(self.name_column, '') or '').strip()
            if not raw_name or raw_name.lower() in ['customer', 'nan', 'none', '', ph.lower()]:
                name = "Customer"
                display_name = "Sir/Madam"
            else:
                name = raw_name
                display_name = raw_name

            if not ph or len(ph) < 7:
                failed_cnt += 1
                self.log_queue.put(("LOG", (f"[{idx+1}/{total}] Invalid phone: '{raw_ph}'", "WARNING")))
                self.log_recipient(ph, name, "FAILED", "Invalid phone number")
                self.log_queue.put(("PROGRESS", (idx + 1, total, sent_cnt, failed_cnt)))
                continue

            if self.dedup_var.get() and ph in processed_phones:
                failed_cnt += 1
                self.log_queue.put(("LOG", (f"[{idx+1}/{total}] Duplicate skipped: {ph}", "WARNING")))
                self.log_recipient(ph, name, "SKIPPED", "Duplicate number")
                self.log_queue.put(("PROGRESS", (idx + 1, total, sent_cnt, failed_cnt)))
                continue

            if ph in blacklisted:
                failed_cnt += 1
                self.log_queue.put(("LOG", (f"[{idx+1}/{total}] Blacklisted skipped: {ph}", "WARNING")))
                self.log_recipient(ph, name, "SKIPPED", "Blacklisted")
                self.log_queue.put(("PROGRESS", (idx + 1, total, sent_cnt, failed_cnt)))
                continue

            processed_phones.add(ph)

            # Personalize with Spintax & Smart Fallback
            custom_msg = parse_spintax(msg_template)
            for col in self.detected_columns:
                val = str(row.get(col, "")).strip()
                if col.lower() == "name" and (not val or val.lower() in ["customer", "none", "nan"]):
                    val = display_name
                custom_msg = custom_msg.replace(f"{{{col}}}", val)
            
            # Universal fallback for {Name} / {name} tags
            custom_msg = re.sub(r'\{name\}', display_name, custom_msg, flags=re.IGNORECASE)

            self.log_queue.put(("LOG", (f"[{idx+1}/{total}] Dispatching to {name} ({ph})...", "INFO")))
            ok, status_msg = self.provider.send_message(ph, custom_msg, self.attachment_path, sim_typing)

            if ok:
                sent_cnt += 1
                self.log_queue.put(("LOG", (f"[{idx+1}/{total}] SENT ✓ to {ph}", "SUCCESS")))
                self.log_recipient(ph, name, "SENT", "Delivered")
            else:
                failed_cnt += 1
                self.log_queue.put(("LOG", (f"[{idx+1}/{total}] FAILED to {ph}: {status_msg}", "ERROR")))
                self.log_recipient(ph, name, "FAILED", status_msg)

            self.log_queue.put(("PROGRESS", (idx + 1, total, sent_cnt, failed_cnt)))

            # Anti-ban delay
            if idx < total - 1 and not self.stop_requested:
                delay = random.uniform(min_d, max_d)
                time.sleep(delay)

        update_campaign_status(self.current_campaign_id, "Completed" if not self.stop_requested else "Failed")
        self.finish_campaign(f"Campaign Completed! Delivered: {sent_cnt} | Failed/Skipped: {failed_cnt}")

    def log_recipient(self, phone, name, status, error_msg=""):
        with get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO campaign_recipients (campaign_id, phone, name, status, sent_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.current_campaign_id, phone, name, status, now, error_msg))
            conn.commit()

    def finish_campaign(self, summary_msg):
        if self.provider:
            self.provider.close()
            self.provider = None
        self.log_queue.put(("FINISH", summary_msg))

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.log_queue.get_nowait()
                if msg_type == "LOG":
                    text, level = data
                    self.append_log(text, level)
                elif msg_type == "PROGRESS":
                    curr, total, sent, failed = data
                    self.progress["value"] = curr
                    self.update_stat_badges(total, sent, failed, total - curr)
                    self.progress_lbl.config(text=f"Processing: {curr}/{total} contacts ({int(curr/total*100)}%)")
                elif msg_type == "FINISH":
                    self.append_log(data, "SUCCESS")
                    messagebox.showinfo("Finished", data)
                    self.campaign_running = False
                    self.campaign_paused = False
                    self.start_btn.config(state="normal")
                    self.browse_btn.config(state="normal")
                    self.pause_btn.config(state="disabled", text="⏸ PAUSE")
                    self.stop_btn.config(state="disabled")
                    self.progress_lbl.config(text="Campaign finished")
                    if hasattr(self, "analytics_view"):
                        self.analytics_view.refresh_analytics()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def append_log(self, text, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(tk.END, f"[{ts}] [{level}] {text}\n", level)
        self.log_box.see(tk.END)

    # =========================================================================
    # TAB 4: TEMPLATES & TAB 5: BLACKLIST
    # =========================================================================
    def build_templates_tab(self):
        container = ttk.Frame(self.tab_templates, style="Card.TFrame")
        container.pack(fill="both", expand=True, padx=15, pady=15)
        ttk.Label(container, text="Message Templates Storage", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 10))

        self.tmpl_tree = ttk.Treeview(container, columns=("ID", "Title", "Created"), show="headings", height=8)
        self.tmpl_tree.heading("ID", text="ID")
        self.tmpl_tree.heading("Title", text="Template Title")
        self.tmpl_tree.heading("Created", text="Date Created")
        self.tmpl_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.refresh_templates()

    def refresh_templates(self):
        for r in self.tmpl_tree.get_children():
            self.tmpl_tree.delete(r)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, created_at FROM templates ORDER BY id DESC")
            for row in cursor.fetchall():
                self.tmpl_tree.insert("", tk.END, values=(row[0], row[1], row[2]))

    def build_blacklist_tab(self):
        container = ttk.Frame(self.tab_blacklist, style="Card.TFrame")
        container.pack(fill="both", expand=True, padx=15, pady=15)
        ttk.Label(container, text="🚫 Opt-Out & Blacklist Management", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(5, 10))

        self.bl_tree = ttk.Treeview(container, columns=("ID", "Phone", "Reason", "Added"), show="headings", height=8)
        self.bl_tree.heading("ID", text="ID")
        self.bl_tree.heading("Phone", text="Phone Number")
        self.bl_tree.heading("Reason", text="Reason / Opt-Out")
        self.bl_tree.heading("Added", text="Date Added")
        self.bl_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.refresh_blacklist()

    def refresh_blacklist(self):
        for r in self.bl_tree.get_children():
            self.bl_tree.delete(r)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, phone, reason, added_at FROM blacklist ORDER BY id DESC")
            for row in cursor.fetchall():
                self.bl_tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3]))

    # =========================================================================
    # TAB 6: LICENSE & PLANS
    # =========================================================================
    def build_license_tab(self):
        container = ttk.Frame(self.tab_license, style="TFrame")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        card1 = ttk.Frame(container, style="Card.TFrame")
        card1.pack(fill="x", pady=(0, 15), ipady=12, ipadx=15)
        ttk.Label(card1, text="🔑 License & Hardware Device Binding", style="CardTitle.TLabel").pack(anchor="w", padx=15, pady=(5, 5))

        m_row = ttk.Frame(card1, style="Card.TFrame")
        m_row.pack(fill="x", padx=15, pady=4)
        ttk.Label(m_row, text="Machine Hardware ID:", style="CardLabel.TLabel").pack(side="left")
        self.mach_val = ttk.Label(m_row, text=get_machine_id(), font=("Consolas", 11, "bold"), foreground=ACCENT_BLUE)
        self.mach_val.pack(side="left", padx=10)

        def copy_m():
            self.root.clipboard_clear()
            self.root.clipboard_append(get_machine_id())
            messagebox.showinfo("Copied", f"Machine ID '{get_machine_id()}' copied to clipboard!")
        ttk.Button(m_row, text="📋 Copy Machine ID", style="Secondary.TButton", command=copy_m).pack(side="left", padx=6)

        def copy_for_seller():
            mach = get_machine_id()
            self.root.clipboard_clear()
            self.root.clipboard_append(mach)
            messagebox.showinfo("Ready to Send", f"Machine ID: {mach}\n\nCopied to clipboard!\nSend this ID to your software seller to receive your activation license key.")
        ttk.Button(m_row, text="📲 Copy for Seller / WhatsApp", style="ActionBlue.TButton", command=copy_for_seller).pack(side="left", padx=4)

        card2 = ttk.Frame(container, style="Card.TFrame")
        card2.pack(fill="x", pady=(0, 15), ipady=12, ipadx=15)
        ttk.Label(card2, text="Activate Commercial Product Key", style="CardTitle.TLabel").pack(anchor="w", padx=15, pady=(5, 5))
        ttk.Label(card2, text="Enter key format (LICENSE-PLAN-YYYYMMDD-MACHID-SIG):", style="CardLabel.TLabel").pack(anchor="w", padx=15, pady=(0, 6))

        act_bar = ttk.Frame(card2, style="Card.TFrame")
        act_bar.pack(fill="x", padx=15, pady=5)
        self.lic_ent = ttk.Entry(act_bar, font=("Consolas", 10, "bold"), width=44)
        self.lic_ent.pack(side="left")

        def do_act():
            k = self.lic_ent.get().strip()
            ok, msg = activate_key(k)
            if ok:
                self.update_header_license_badge()
                messagebox.showinfo("Activated", msg)
            else:
                messagebox.showerror("Activation Failed", msg)

        def do_deact():
            if messagebox.askyesno("Deactivate", "Revert to Free Trial?"):
                deactivate_license()
                self.update_header_license_badge()

        ttk.Button(act_bar, text="⚡ Activate Key", style="Primary.TButton", command=do_act).pack(side="left", padx=6)
        ttk.Button(act_bar, text="❌ Deactivate", style="Danger.TButton", command=do_deact).pack(side="left")


if __name__ == "__main__":
    root = tk.Tk()
    app = WhatsAppEnterpriseApp(root)
    root.mainloop()
