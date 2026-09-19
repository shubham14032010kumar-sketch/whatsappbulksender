"""
SHAKTIX Design System & Enterprise UI Theme (ui/theme.py)
Brand Identity: Shakti Orange (#FF6B00) + Royal Violet (#7C3AED)
"""

from tkinter import ttk

SHAKTIX_THEME = {
    "brand_primary": "#FF6B00",
    "brand_secondary": "#7C3AED",
    "bg_base": "#0B0F19",
    "bg_surface": "#131826",
    "bg_elevated": "#1B2233",
    "border": "#263049",
    "text_primary": "#F5F7FA",
    "text_muted": "#8A94AD",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "info": "#38BDF8",
    "radius": 14,
}

BG_DARK = SHAKTIX_THEME["bg_base"]
BG_CARD = SHAKTIX_THEME["bg_surface"]
BG_LIGHT = SHAKTIX_THEME["bg_elevated"]
BORDER_COLOR = SHAKTIX_THEME["border"]

TEXT_LIGHT = SHAKTIX_THEME["text_primary"]
TEXT_MUTED = SHAKTIX_THEME["text_muted"]

ACCENT_ORANGE = SHAKTIX_THEME["brand_primary"]
ACCENT_PURPLE = SHAKTIX_THEME["brand_secondary"]
ACCENT_BLUE = "#3b82f6"
ACCENT_GREEN = SHAKTIX_THEME["success"]
ACCENT_RED = SHAKTIX_THEME["danger"]
ACCENT_AMBER = SHAKTIX_THEME["warning"]
ACCENT_CYAN = SHAKTIX_THEME["info"]


def apply_theme(root):
    """Configures the complete TTK styling suite with SHAKTIX Enterprise Design Tokens."""
    root.configure(bg=BG_DARK)
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("TFrame", background=BG_DARK)
    style.configure("Card.TFrame", background=BG_CARD, relief="flat")
    
    style.configure("TNotebook", background=BG_DARK, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_LIGHT, padding=[16, 9], font=("Segoe UI", 10, "bold"))
    style.map("TNotebook.Tab", background=[("selected", ACCENT_ORANGE)], foreground=[("selected", "#ffffff")])

    style.configure("Header.TLabel", background=BG_DARK, foreground=TEXT_LIGHT, font=("Segoe UI", 16, "bold"))
    style.configure("SubHeader.TLabel", background=BG_DARK, foreground=ACCENT_ORANGE, font=("Segoe UI", 9, "bold"))
    style.configure("CardTitle.TLabel", background=BG_CARD, foreground=TEXT_LIGHT, font=("Segoe UI", 11, "bold"))
    style.configure("CardLabel.TLabel", background=BG_CARD, foreground=TEXT_MUTED, font=("Segoe UI", 9))

    style.configure("Badge.TLabel", background=BG_LIGHT, foreground=TEXT_LIGHT, font=("Segoe UI", 10, "bold"), padding=[10, 5])
    style.configure("SuccessBadge.TLabel", background="#064e3b", foreground="#6ee7b7", font=("Segoe UI", 10, "bold"), padding=[10, 5])
    style.configure("WarningBadge.TLabel", background="#78350f", foreground="#fcd34d", font=("Segoe UI", 10, "bold"), padding=[10, 5])
    style.configure("DangerBadge.TLabel", background="#7f1d1d", foreground="#fca5a5", font=("Segoe UI", 10, "bold"), padding=[10, 5])

    style.configure("Primary.TButton", background=ACCENT_ORANGE, foreground="#ffffff", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=[12, 6])
    style.map("Primary.TButton", background=[("active", "#e05e00")])

    style.configure("Secondary.TButton", background=BG_LIGHT, foreground=TEXT_LIGHT, font=("Segoe UI", 9), borderwidth=1, padding=[8, 4])
    style.map("Secondary.TButton", background=[("active", "#2d3748")])

    style.configure("Danger.TButton", background=ACCENT_RED, foreground="#ffffff", font=("Segoe UI", 9, "bold"), borderwidth=0, padding=[8, 4])
    style.map("Danger.TButton", background=[("active", "#dc2626")])

    style.configure("ActionGreen.TButton", background=ACCENT_GREEN, foreground="#ffffff", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=[14, 8])
    style.map("ActionGreen.TButton", background=[("active", "#059669")])

    style.configure("ActionBlue.TButton", background=ACCENT_PURPLE, foreground="#ffffff", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=[12, 6])
    style.map("ActionBlue.TButton", background=[("active", "#6d28d9")])

    style.configure("Treeview", background=BG_CARD, foreground=TEXT_LIGHT, fieldbackground=BG_CARD, borderwidth=0, font=("Segoe UI", 9))
    style.map("Treeview", background=[("selected", ACCENT_ORANGE)], foreground=[("selected", "#ffffff")])
    style.configure("Treeview.Heading", background=BG_LIGHT, foreground=TEXT_LIGHT, font=("Segoe UI", 9, "bold"))

    style.configure("TProgressbar", thickness=10, troughcolor=BG_LIGHT, background=ACCENT_ORANGE)
