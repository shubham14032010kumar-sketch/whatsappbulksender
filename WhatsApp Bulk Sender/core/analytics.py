"""
Advanced Analytics & Reporting Engine (core/analytics.py)
Computes real-time KPI metrics, failure distributions, delivery success rates,
and exports executive PDF/HTML and CSV reports.
"""

from datetime import datetime
from core.db import get_connection


def get_dashboard_metrics():
    """Computes high-level business analytics across CRM and Campaigns."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM contacts")
        total_contacts = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM contacts WHERE opt_in = 0")
        opt_outs = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM campaigns")
        total_campaigns = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM campaigns WHERE status = 'Running'")
        active_campaigns = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COALESCE(SUM(sent_count), 0), COALESCE(SUM(failed_count), 0) FROM campaigns")
        row = cursor.fetchone()
        processed_sent = row[0] or 0
        processed_failed = row[1] or 0

        total_processed = processed_sent + processed_failed
        success_rate = round((processed_sent / total_processed * 100), 1) if total_processed > 0 else 0.0

        return {
            "total_contacts": total_contacts,
            "opt_outs": opt_outs,
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "total_sent": processed_sent,
            "total_failed": processed_failed,
            "total_processed": total_processed,
            "success_rate": success_rate
        }


def get_campaign_analytics(campaign_id):
    """Fetches detailed analytics breakdown for a single campaign."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, status, scheduled_at, total_recipients, sent_count, failed_count, created_at
            FROM campaigns WHERE id = ?
        """, (campaign_id,))
        camp = cursor.fetchone()
        if not camp:
            return None

        cursor.execute("""
            SELECT status, COUNT(*) as cnt
            FROM campaign_recipients
            WHERE campaign_id = ?
            GROUP BY status
        """, (campaign_id,))
        status_breakdown = {r["status"]: r["cnt"] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT error_message, COUNT(*) as cnt
            FROM campaign_recipients
            WHERE campaign_id = ? AND status = 'FAILED' AND error_message IS NOT NULL
            GROUP BY error_message
        """, (campaign_id,))
        error_breakdown = {r["error_message"]: r["cnt"] for r in cursor.fetchall()}

        total = camp["total_recipients"] or 0
        sent = camp["sent_count"] or 0
        failed = camp["failed_count"] or 0
        rate = round((sent / (sent + failed) * 100), 1) if (sent + failed) > 0 else 0.0

        return {
            "campaign": dict(camp),
            "status_breakdown": status_breakdown,
            "error_breakdown": error_breakdown,
            "success_rate": rate
        }


def generate_printable_html_report(campaign_id):
    """Generates a professional standalone HTML report with KPIs and recipient audit table."""
    analytics = get_campaign_analytics(campaign_id)
    if not analytics:
        return "<h3>Campaign not found</h3>"

    c = analytics["campaign"]
    recipients = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT phone, name, status, sent_at, error_message FROM campaign_recipients WHERE campaign_id = ?", (campaign_id,))
        recipients = [dict(r) for r in cursor.fetchall()]

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Campaign Report - {c['name']}</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #1e293b; background: #f8fafc; }}
        .header {{ border-bottom: 2px solid #3b82f6; padding-bottom: 15px; margin-bottom: 25px; }}
        h1 {{ color: #0f172a; margin: 0; }}
        .meta {{ color: #64748b; font-size: 14px; margin-top: 5px; }}
        .grid {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .card {{ background: #fff; padding: 18px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1; }}
        .card-val {{ font-size: 26px; font-weight: bold; color: #0f172a; margin-top: 6px; }}
        .green {{ color: #10b981; }}
        .red {{ color: #ef4444; }}
        .blue {{ color: #3b82f6; }}
        table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
        th {{ background: #f1f5f9; color: #475569; font-weight: 600; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .badge-SENT {{ background: #dcfce7; color: #15803d; }}
        .badge-FAILED {{ background: #fee2e2; color: #b91c1c; }}
        .badge-SKIPPED {{ background: #fef3c7; color: #b45309; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 WhatsApp Campaign Audit Report</h1>
        <div class="meta">Campaign: <strong>{c['name']}</strong> | Date: {c['created_at']} | Status: {c['status']}</div>
    </div>

    <div class="grid">
        <div class="card">
            <div>Total Target Audience</div>
            <div class="card-val blue">{c['total_recipients']}</div>
        </div>
        <div class="card">
            <div>Successfully Delivered</div>
            <div class="card-val green">{c['sent_count']}</div>
        </div>
        <div class="card">
            <div>Failed / Undelivered</div>
            <div class="card-val red">{c['failed_count']}</div>
        </div>
        <div class="card">
            <div>Success Rate</div>
            <div class="card-val green">{analytics['success_rate']}%</div>
        </div>
    </div>

    <h2>Recipient Audit Log ({len(recipients)} Records)</h2>
    <table>
        <thead>
            <tr>
                <th>Phone / WhatsApp</th>
                <th>Recipient Name</th>
                <th>Delivery Status</th>
                <th>Timestamp</th>
                <th>Notes / Error</th>
            </tr>
        </thead>
        <tbody>
    """

    for r in recipients:
        st = r["status"]
        html += f"""
            <tr>
                <td><strong>{r['phone']}</strong></td>
                <td>{r['name'] or 'Customer'}</td>
                <td><span class="badge badge-{st}">{st}</span></td>
                <td>{r['sent_at'] or '-'}</td>
                <td>{r['error_message'] or 'Delivered'}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
</body>
</html>"""
    return html
