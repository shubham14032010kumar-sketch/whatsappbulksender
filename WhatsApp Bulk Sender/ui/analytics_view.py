"""
Advanced Analytics Dashboard & Reports View (ui/analytics_view.py)
Visualizes platform KPIs, campaign performance comparisons,
failure distributions, and generates executive printable reports.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from core.analytics import get_dashboard_metrics, get_campaign_analytics, generate_printable_html_report
from core.campaign_engine import get_all_campaigns


class AnalyticsDashboardFrame(ttk.Frame):
    """Analytics & Reporting Dashboard View."""

    def __init__(self, parent):
        super().__init__(parent, style="TFrame")
        self.pack(fill="both", expand=True, padx=15, pady=10)

        # 1. Top KPI Summary
        self.build_kpi_row()

        # 2. Main Analytics Split Pane
        self.build_details_section()

        self.refresh_analytics()

    def build_kpi_row(self):
        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(fill="x", pady=(0, 10), ipady=8, ipadx=10)

        ttk.Label(card, text="📈 Executive Performance Dashboard", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(2, 8))

        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x", padx=10)

        self.kpi_total_camps = ttk.Label(row, text="Total Campaigns: 0", style="StatBlue.TLabel")
        self.kpi_total_camps.pack(side="left", expand=True, fill="x", padx=3)

        self.kpi_sent = ttk.Label(row, text="Delivered: 0", style="StatGreen.TLabel")
        self.kpi_sent.pack(side="left", expand=True, fill="x", padx=3)

        self.kpi_failed = ttk.Label(row, text="Failed: 0", style="StatRed.TLabel")
        self.kpi_failed.pack(side="left", expand=True, fill="x", padx=3)

        self.kpi_rate = ttk.Label(row, text="Success Rate: 0%", style="StatGreen.TLabel")
        self.kpi_rate.pack(side="left", expand=True, fill="x", padx=3)

        self.kpi_optouts = ttk.Label(row, text="Opt-outs: 0", style="StatYellow.TLabel")
        self.kpi_optouts.pack(side="left", expand=True, fill="x", padx=3)

    def build_details_section(self):
        container = ttk.Frame(self, style="TFrame")
        container.pack(fill="both", expand=True)

        left = ttk.Frame(container, style="Card.TFrame")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8), ipady=6, ipadx=10)

        right = ttk.Frame(container, style="Card.TFrame")
        right.pack(side="right", fill="both", expand=True, padx=(8, 0), ipady=6, ipadx=10)

        # Left Column: Campaign Selection Table
        l_header = ttk.Frame(left, style="Card.TFrame")
        l_header.pack(fill="x", padx=10, pady=(4, 6))
        ttk.Label(l_header, text="Select Campaign for Audit Breakdown", style="CardTitle.TLabel").pack(side="left")
        ttk.Button(l_header, text="🔄 Refresh", style="Secondary.TButton", command=self.refresh_analytics).pack(side="right")

        tree_f = ttk.Frame(left, style="Card.TFrame")
        tree_f.pack(fill="both", expand=True, padx=10, pady=4)

        cols = ("ID", "Campaign Name", "Status", "Audience", "Sent", "Failed", "Date")
        self.camp_tree = ttk.Treeview(tree_f, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.camp_tree.heading(c, text=c)
            self.camp_tree.column(c, width=90)
        self.camp_tree.column("ID", width=40)
        self.camp_tree.column("Campaign Name", width=160)
        self.camp_tree.pack(side="left", fill="both", expand=True)

        self.camp_tree.bind("<<TreeviewSelect>>", self.on_campaign_selected)

        # Right Column: Campaign Performance & Failure Breakdown
        ttk.Label(right, text="Campaign Performance & Delivery Audit", style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(4, 6))

        self.camp_name_lbl = ttk.Label(right, text="Select a campaign on the left", style="CardVal.TLabel")
        self.camp_name_lbl.pack(anchor="w", padx=10, pady=(0, 6))

        # Visual Canvas Bar for Delivery vs Failures
        self.canvas = tk.Canvas(right, height=36, bg="#0b1120", highlightthickness=0)
        self.canvas.pack(fill="x", padx=10, pady=(0, 10))

        # Failure Reasons Box
        ttk.Label(right, text="Failure Reasons Distribution:", style="CardLabel.TLabel").pack(anchor="w", padx=10)
        self.fail_box = tk.Listbox(right, bg="#0b1120", fg="#f87171", font=("Consolas", 9), height=7)
        self.fail_box.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        # Export Buttons
        btn_bar = ttk.Frame(right, style="Card.TFrame")
        btn_bar.pack(fill="x", padx=10, pady=5)

        self.btn_export_html = ttk.Button(btn_bar, text="📄 Export Executive HTML Report", style="Primary.TButton", command=self.export_html_report, state="disabled")
        self.btn_export_html.pack(side="left", padx=(0, 4))

        self.selected_camp_id = None

    def refresh_analytics(self):
        m = get_dashboard_metrics()
        self.kpi_total_camps.config(text=f"Campaigns: {m['total_campaigns']}")
        self.kpi_sent.config(text=f"Delivered: {m['total_sent']}")
        self.kpi_failed.config(text=f"Failed: {m['total_failed']}")
        self.kpi_rate.config(text=f"Success Rate: {m['success_rate']}%")
        self.kpi_optouts.config(text=f"Opt-outs: {m['opt_outs']}")

        for r in self.camp_tree.get_children():
            self.camp_tree.delete(r)

        camps = get_all_campaigns()
        for c in camps:
            self.camp_tree.insert("", tk.END, values=(
                c["id"], c["name"], c["status"], c["total_recipients"], c["sent_count"], c["failed_count"], c["created_at"]
            ))

    def on_campaign_selected(self, event):
        sel = self.camp_tree.selection()
        if not sel:
            return
        cid = self.camp_tree.item(sel[0])["values"][0]
        self.selected_camp_id = cid
        self.btn_export_html.config(state="normal")

        analytics = get_campaign_analytics(cid)
        if not analytics:
            return

        c = analytics["campaign"]
        self.camp_name_lbl.config(text=f"{c['name']} (Delivered: {c['sent_count']} | Failed: {c['failed_count']} | {analytics['success_rate']}%)")

        # Draw delivery progress bar on canvas
        self.canvas.delete("all")
        w = self.canvas.winfo_width() or 300
        h = 36
        total = max(1, c["total_recipients"] or 1)
        sent_w = int((c["sent_count"] / total) * w)
        fail_w = int((c["failed_count"] / total) * w)

        if sent_w > 0:
            self.canvas.create_rectangle(0, 0, sent_w, h, fill="#10b981", outline="")
        if fail_w > 0:
            self.canvas.create_rectangle(sent_w, 0, sent_w + fail_w, h, fill="#ef4444", outline="")

        # List failure reasons
        self.fail_box.delete(0, tk.END)
        if analytics["error_breakdown"]:
            for reason, cnt in analytics["error_breakdown"].items():
                self.fail_box.insert(tk.END, f"• {cnt}x — {reason}")
        else:
            self.fail_box.insert(tk.END, "✓ No recorded delivery errors for this campaign.")

    def export_html_report(self):
        if not self.selected_camp_id:
            return
        html = generate_printable_html_report(self.selected_camp_id)
        path = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML Report", "*.html")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            messagebox.showinfo("Report Exported", f"Executive report saved to:\n{path}")
