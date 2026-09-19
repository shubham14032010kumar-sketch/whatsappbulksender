"""
Visual Campaign Builder & Campaign Workspace (ui/campaign_wizard.py)
Implements 5-Step Campaign Creation Wizard:
Audience -> Template & Message -> Media -> Schedule & Delays -> Review & Launch
along with Campaign lifecycle state tracking.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import re
from datetime import datetime

from core.campaign_engine import create_campaign, get_all_campaigns, update_campaign_status
from core.licensing import get_active_license
from core.audit import log_audit

try:
    import pandas as pd
except ImportError:
    pd = None


class VisualCampaignWizardDialog:
    """5-Step Interactive Visual Campaign Builder Dialog."""

    def __init__(self, parent, preloaded_contacts=None, on_launch_callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("Visual Campaign Builder — Enterprise Wizard")
        self.top.geometry("680x560")
        self.top.configure(bg="#090d16")
        self.top.transient(parent)
        self.top.grab_set()

        self.preloaded_contacts = preloaded_contacts or []
        self.on_launch = on_launch_callback
        self.current_step = 0
        self.attachment_path = None

        # Header Title
        h_frame = ttk.Frame(self.top)
        h_frame.pack(fill="x", padx=25, pady=(15, 5))

        self.step_badge = ttk.Label(h_frame, text="Step 1 of 5: Audience", style="StatBlue.TLabel")
        self.step_badge.pack(side="left")

        self.step_title = ttk.Label(h_frame, text="Select Target Audience", style="Header.TLabel")
        self.step_title.pack(side="left", padx=15)

        # Main Step Container
        self.container = ttk.Frame(self.top, style="Card.TFrame")
        self.container.pack(fill="both", expand=True, padx=25, pady=10)

        # Nav Buttons
        nav = ttk.Frame(self.top)
        nav.pack(fill="x", padx=25, pady=(0, 15))

        self.btn_back = ttk.Button(nav, text="← Back", style="Secondary.TButton", command=self.prev_step, state="disabled")
        self.btn_back.pack(side="left")

        self.btn_next = ttk.Button(nav, text="Next Step →", style="Primary.TButton", command=self.next_step)
        self.btn_next.pack(side="right")

        # Variables
        self.camp_name_var = tk.StringVar(value=f"Campaign_{datetime.now().strftime('%b%d_%H%M')}")
        self.min_delay_var = tk.StringVar(value="8")
        self.max_delay_var = tk.StringVar(value="15")
        self.schedule_time_var = tk.StringVar(value="")
        self.is_scheduled_var = tk.BooleanVar(value=False)
        self.sim_typing_var = tk.BooleanVar(value=True)

        self.render_current_step()

    def clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def render_current_step(self):
        self.clear_container()

        if self.current_step == 0:
            self.render_step_audience()
        elif self.current_step == 1:
            self.render_step_message()
        elif self.current_step == 2:
            self.render_step_media()
        elif self.current_step == 3:
            self.render_step_schedule()
        elif self.current_step == 4:
            self.render_step_review()

        self.btn_back.config(state="normal" if self.current_step > 0 else "disabled")
        if self.current_step == 4:
            self.btn_next.config(text="🚀 Launch Campaign Now", style="ActionBlue.TButton")
        else:
            self.btn_next.config(text="Next Step →", style="Primary.TButton")

    # Step 1: Audience Selection
    def render_step_audience(self):
        self.step_badge.config(text="Step 1 of 5: Audience")
        self.step_title.config(text="Target Audience & Campaign Name")

        f = ttk.Frame(self.container, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=20, pady=15)

        ttk.Label(f, text="Campaign Name:", style="CardLabel.TLabel").pack(anchor="w", pady=(0, 2))
        ttk.Entry(f, textvariable=self.camp_name_var, width=35).pack(fill="x", pady=(0, 15))

        count = len(self.preloaded_contacts)
        ttk.Label(f, text=f"Selected Audience Source: {count} Contacts Loaded", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))

        box = tk.Listbox(f, bg="#0b1120", fg="#f8fafc", font=("Segoe UI", 9), height=9)
        box.pack(fill="both", expand=True, pady=(0, 10))

        if self.preloaded_contacts:
            for idx, c in enumerate(self.preloaded_contacts[:50]):
                nm = c.get("name") or "Customer"
                ph = c.get("phone") or ""
                cty = c.get("city") or ""
                cat = c.get("category") or ""
                box.insert(tk.END, f"{idx+1}. {nm} ({ph}) — {cty} | {cat}")
            if count > 50:
                box.insert(tk.END, f"... and {count - 50} more contacts")
        else:
            box.insert(tk.END, "⚠️ No contacts currently loaded! Please import contacts or choose from CRM.")

    # Step 2: Message & Personalization
    def render_step_message(self):
        self.step_badge.config(text="Step 2 of 5: Message")
        self.step_title.config(text="Craft Personalized Message")

        f = ttk.Frame(self.container, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=20, pady=10)

        # Tags insertion bar
        tags_bar = ttk.Frame(f, style="Card.TFrame")
        tags_bar.pack(fill="x", pady=(0, 6))
        ttk.Label(tags_bar, text="Tags:", style="CardLabel.TLabel").pack(side="left", padx=(0, 4))

        for tag in ["{Name}", "{Phone}", "{City}", "{Company}", "{Category}"]:
            btn = ttk.Button(tags_bar, text=tag, style="Secondary.TButton", width=10, command=lambda t=tag: self.msg_text.insert(tk.INSERT, t))
            btn.pack(side="left", padx=2)

        self.msg_text = scrolledtext.ScrolledText(f, height=10, bg="#0b1120", fg="#f8fafc", insertbackground="#fff", font=("Segoe UI", 10))
        self.msg_text.pack(fill="both", expand=True, pady=(0, 6))

        if not hasattr(self, "saved_msg") or not self.saved_msg:
            self.msg_text.insert(tk.END, "{Hello|Hi|Greetings} {Name},\n\nWe hope this finds you well. We are pleased to share our exclusive updates with you.\n\nBest Regards,\nTeam")
        else:
            self.msg_text.insert(tk.END, self.saved_msg)

        ttk.Label(f, text="💡 Tip: Spintax like {Hello|Hi|Greetings} randomly rotates words to prevent duplicate flags.", foreground="#94a3b8", font=("Segoe UI", 9)).pack(anchor="w")

    # Step 3: Media & Attachments
    def render_step_media(self):
        self.step_badge.config(text="Step 3 of 5: Media")
        self.step_title.config(text="Add Media Attachments")

        f = ttk.Frame(self.container, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=20, pady=20)

        ttk.Label(f, text="Attach an Image, PDF, Brochure, or Video:", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 10))

        m_bar = ttk.Frame(f, style="Card.TFrame")
        m_bar.pack(fill="x", pady=10)

        def pick_file():
            p = filedialog.askopenfilename(title="Select Media File", filetypes=[("All Media", "*.jpg *.png *.jpeg *.webp *.pdf *.mp4 *.docx")])
            if p:
                self.attachment_path = p
                self.media_lbl.config(text=p)

        def clear_file():
            self.attachment_path = None
            self.media_lbl.config(text="No media attached (Text-only message)")

        ttk.Button(m_bar, text="📎 Select Attachment", style="Primary.TButton", command=pick_file).pack(side="left")
        ttk.Button(m_bar, text="Clear", style="Secondary.TButton", command=clear_file).pack(side="left", padx=6)

        self.media_lbl = ttk.Label(f, text=self.attachment_path or "No media attached (Text-only message)", style="CardLabel.TLabel", wraplength=480)
        self.media_lbl.pack(anchor="w", pady=10)

    # Step 4: Schedule & Delays
    def render_step_schedule(self):
        self.step_badge.config(text="Step 4 of 5: Timing")
        self.step_title.config(text="Anti-Ban Speed & Scheduling")

        f = ttk.Frame(self.container, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=20, pady=15)

        ttk.Label(f, text="Anti-Ban Dispatch Delay (Seconds):", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 6))

        d_row = ttk.Frame(f, style="Card.TFrame")
        d_row.pack(fill="x", pady=(0, 15))

        ttk.Entry(d_row, textvariable=self.min_delay_var, width=5).pack(side="left", padx=(0, 4))
        ttk.Label(d_row, text="to", style="CardLabel.TLabel").pack(side="left", padx=4)
        ttk.Entry(d_row, textvariable=self.max_delay_var, width=5).pack(side="left", padx=(4, 0))
        ttk.Label(d_row, text="sec per message", style="CardLabel.TLabel").pack(side="left", padx=6)

        ttk.Checkbutton(f, text="Enable Human Keystroke Simulator", variable=self.sim_typing_var).pack(anchor="w", pady=(0, 15))

        ttk.Label(f, text="Automated Schedule Dispatch:", style="CardTitle.TLabel").pack(anchor="w", pady=(5, 6))

        s_row = ttk.Frame(f, style="Card.TFrame")
        s_row.pack(fill="x")
        ttk.Checkbutton(s_row, text="Schedule for later today (24hr HH:MM):", variable=self.is_scheduled_var).pack(side="left")
        s_ent = ttk.Entry(s_row, textvariable=self.schedule_time_var, width=8)
        s_ent.pack(side="left", padx=6)
        if not self.schedule_time_var.get():
            self.schedule_time_var.set("15:00")

    # Step 5: Review & Launch
    def render_step_review(self):
        self.step_badge.config(text="Step 5 of 5: Review")
        self.step_title.config(text="Pre-Flight Review & Launch")

        f = ttk.Frame(self.container, style="Card.TFrame")
        f.pack(fill="both", expand=True, padx=20, pady=12)

        c_name = self.camp_name_var.get()
        count = len(self.preloaded_contacts)
        msg_preview = getattr(self, "saved_msg", "")[:120] + "..."
        sched = self.schedule_time_var.get() if self.is_scheduled_var.get() else "Immediate Launch"
        att = self.attachment_path or "None (Text Only)"

        review_items = [
            ("Campaign Name:", c_name),
            ("Target Audience:", f"{count} Recipients"),
            ("Dispatch Schedule:", sched),
            ("Anti-Ban Delays:", f"{self.min_delay_var.get()} - {self.max_delay_var.get()} sec"),
            ("Attachment:", att),
            ("Message Template:", msg_preview)
        ]

        for lbl, val in review_items:
            r = ttk.Frame(f, style="Card.TFrame")
            r.pack(fill="x", pady=3)
            ttk.Label(r, text=lbl, style="CardLabel.TLabel", width=18).pack(side="left")
            ttk.Label(r, text=val, style="CardVal.TLabel").pack(side="left", fill="x", expand=True)

    def next_step(self):
        if self.current_step == 1:
            self.saved_msg = self.msg_text.get("1.0", tk.END).strip()
            if not self.saved_msg:
                messagebox.showwarning("Empty Template", "Please enter a message template.")
                return

        if self.current_step < 4:
            self.current_step += 1
            self.render_current_step()
        else:
            self.execute_launch()

    def prev_step(self):
        if self.current_step > 0:
            if self.current_step == 1:
                self.saved_msg = self.msg_text.get("1.0", tk.END).strip()
            self.current_step -= 1
            self.render_current_step()

    def execute_launch(self):
        if not self.preloaded_contacts:
            messagebox.showerror("No Audience", "Cannot launch campaign with 0 recipients.")
            return

        c_name = self.camp_name_var.get()
        min_d = int(self.min_delay_var.get() or "8")
        max_d = int(self.max_delay_var.get() or "15")
        sched = self.schedule_time_var.get() if self.is_scheduled_var.get() else None

        camp_id = create_campaign(
            c_name, scheduled_at=sched, min_delay=min_d, max_delay=max_d,
            recipient_list=self.preloaded_contacts
        )

        self.top.destroy()
        if self.on_launch:
            self.on_launch({
                "campaign_id": camp_id,
                "name": c_name,
                "template": getattr(self, "saved_msg", ""),
                "attachment": self.attachment_path,
                "min_delay": min_d,
                "max_delay": max_d,
                "scheduled_at": sched,
                "sim_typing": self.sim_typing_var.get(),
                "contacts": self.preloaded_contacts
            })
