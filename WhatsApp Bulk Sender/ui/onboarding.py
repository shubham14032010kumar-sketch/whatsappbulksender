"""
6-Step First-Time User Onboarding Wizard (ui/onboarding.py)
Guides new commercial customers through configuration and best practices.
"""

import tkinter as tk
from tkinter import ttk

ONBOARDING_STEPS = [
    {
        "title": "Welcome to WhatsApp Bulk Sender 👋",
        "badge": "Step 1 of 6: Overview & Profile",
        "text": "Welcome to your Enterprise WhatsApp Marketing & CRM platform!\n\n"
                "• Dedicated CRM with groups, tags, and custom fields\n"
                "• Visual campaign builder with anti-ban safeguards\n"
                "• Live delivery analytics and audit reports\n"
                "• Full offline/online licensing protection"
    },
    {
        "title": "📇 Build Your Contact Database",
        "badge": "Step 2 of 6: Contacts & Import",
        "text": "Easily organize your audience in the CRM:\n\n"
                "1. Upload Excel (.xlsx) or CSV files directly into the CRM database.\n"
                "2. The system automatically detects Name, Phone, City, and Categories.\n"
                "3. Numbers are automatically cleaned and deduplicated."
    },
    {
        "title": "🏷️ Organize with Groups & Tags",
        "badge": "Step 3 of 6: Audience Segmentation",
        "text": "Segment your contacts for maximum conversion:\n\n"
                "• Groups: Categorize by industry (Hotels, Doctors, Real Estate)\n"
                "• Tags: Mark lead warmth (Hot Lead, Follow-up, VIP)\n"
                "• Instant Filter: Filter by City + Category + Tag with 1-click launch!"
    },
    {
        "title": "✍️ Personalize with Message Templates",
        "badge": "Step 4 of 6: Dynamic Templates",
        "text": "Make every message personalized and anti-ban compliant:\n\n"
                "• Dynamic Tags: Use {Name}, {City}, {Company}, {Category}\n"
                "• Spintax Variations: Use {Hello|Hi|Greetings} to avoid duplicate patterns\n"
                "• Rich Attachments: Send Images, PDFs, and Videos with captions"
    },
    {
        "title": "🛡️ Anti-Ban Engine & Safety First",
        "badge": "Step 5 of 6: WhatsApp Safety Safeguards",
        "text": "Protect your WhatsApp phone number reputation:\n\n"
                "• Maintain 8 to 15 seconds randomized delay between messages\n"
                "• Enable human-like keystroke typing simulation\n"
                "• Set batch cooldowns (e.g. rest 3 minutes after 30 messages)\n"
                "• Always message opted-in customers"
    },
    {
        "title": "🚀 Ready to Launch Your First Campaign!",
        "badge": "Step 6 of 6: Launch & Reports",
        "text": "You are ready to begin:\n\n"
                "1. Select your target audience in the CRM.\n"
                "2. Click 'Send Campaign to Filtered Audience'.\n"
                "3. Preview your message and click Start Campaign!\n\n"
                "Your persistent QR session will stay saved for all future runs."
    }
]


class OnboardingWizardDialog:
    """Multi-step modal dialog for new users."""

    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Getting Started — Enterprise Onboarding")
        self.top.geometry("540x400")
        self.top.configure(bg="#090d16")
        self.top.transient(parent)
        self.top.grab_set()

        self.current_step = 0

        # UI Elements
        self.badge_lbl = ttk.Label(self.top, text="", style="StatBlue.TLabel")
        self.badge_lbl.pack(pady=(20, 10))

        self.title_lbl = ttk.Label(self.top, text="", style="Header.TLabel")
        self.title_lbl.pack(pady=(0, 15))

        card = ttk.Frame(self.top, style="Card.TFrame")
        card.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self.content_lbl = ttk.Label(card, text="", style="CardLabel.TLabel", font=("Segoe UI", 10), justify="left", wraplength=460)
        self.content_lbl.pack(fill="both", expand=True, padx=20, pady=20)

        # Bottom Navigation
        nav_frame = ttk.Frame(self.top)
        nav_frame.pack(fill="x", padx=30, pady=(0, 20))

        self.prev_btn = ttk.Button(nav_frame, text="← Previous", style="Secondary.TButton", command=self.prev_step)
        self.prev_btn.pack(side="left")

        self.next_btn = ttk.Button(nav_frame, text="Next →", style="Primary.TButton", command=self.next_step)
        self.next_btn.pack(side="right")

        self.render_step()

    def render_step(self):
        s = ONBOARDING_STEPS[self.current_step]
        self.badge_lbl.config(text=s["badge"])
        self.title_lbl.config(text=s["title"])
        self.content_lbl.config(text=s["text"])

        self.prev_btn.config(state="normal" if self.current_step > 0 else "disabled")
        if self.current_step == len(ONBOARDING_STEPS) - 1:
            self.next_btn.config(text="Finish & Start 🚀", style="Primary.TButton")
        else:
            self.next_btn.config(text="Next →", style="Primary.TButton")

    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.render_step()

    def next_step(self):
        if self.current_step < len(ONBOARDING_STEPS) - 1:
            self.current_step += 1
            self.render_step()
        else:
            self.top.destroy()
