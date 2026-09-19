import os
import sqlite3
import random
from datetime import datetime

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(DEMO_DIR)
DB_PATH = os.path.join(PROJECT_DIR, "app_data.db")

def seed_demo_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cities = ["Gaya", "Patna", "Delhi", "Ranchi", "Varanasi", "Kolkata"]
    categories = ["Hotel", "Restaurant", "Retail", "Real Estate", "Education", "Healthcare", "E-commerce"]
    first_names = ["Rahul", "Amit", "Priya", "Vikram", "Sneha", "Anjali", "Ravi", "Sunil", "Pooja", "Deepak", "Neha", "Rohit", "Manish", "Kavita", "Suresh", "Alok", "Nisha", "Gaurav"]
    last_names = ["Sharma", "Verma", "Singh", "Kumar", "Gupta", "Yadav", "Mishra", "Patel", "Jha", "Choudhary", "Pandey"]

    print("[SHAKTIX DEMO] Generating 250 high-quality commercial demo leads...")
    leads = []
    base_phone = 9871000000
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for i in range(250):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        name = f"{fn} {ln}"
        phone = f"91{base_phone + i}"
        city = random.choice(cities)
        cat = random.choice(categories)
        company = f"{ln} {cat} Enterprises"
        tag = random.choice(["Website Lead", "VIP Client", "Retail Partner", "Follow Up", "Cold Outreach", "Hot Prospect"])
        email = f"{fn.lower()}.{ln.lower()}{random.randint(10,99)}@gmail.com"
        leads.append((name, phone, company, city, cat, tag, 1, now, now, 1, email, "New Lead"))

    cursor.executemany("""
    INSERT OR IGNORE INTO contacts (name, phone, company, city, category, tags, opt_in, created_at, updated_at, org_id, email, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, leads)

    print("[SHAKTIX DEMO] Seeding 12 Pre-built Commercial Campaigns...")
    sample_campaigns = [
        ("Diwali VIP Exclusive Launch", "Completed", 850, 810, 40),
        ("Gaya Hotel & Hospitality Outreach", "Completed", 320, 305, 15),
        ("Patna Retail Expo Invitation", "Completed", 640, 598, 42),
        ("Real Estate Investor Broadcast", "Completed", 450, 412, 38),
        ("Delhi Enterprise B2B Webinar", "Completed", 1200, 1140, 60),
        ("Healthcare Checkup Awareness", "Completed", 500, 485, 15),
        ("Education & Coaching Admission Drive", "Completed", 920, 880, 40),
        ("E-commerce Weekend Flash Sale", "Completed", 1500, 1420, 80),
        ("Corporate Renewal Follow-up", "Completed", 180, 178, 2),
        ("Automotive Test Drive Campaign", "Completed", 410, 390, 20),
        ("FMCG Distributor Expansion", "Running", 600, 340, 12),
        ("SHAKTIX Product Demo Showcase", "Scheduled", 250, 0, 0)
    ]

    for camp in sample_campaigns:
        cursor.execute("""
        INSERT INTO campaigns (org_id, name, status, total_recipients, sent_count, failed_count, created_at, updated_at)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?)
        """, (camp[0], camp[1], camp[2], camp[3], camp[4], now, now))

    conn.commit()
    conn.close()

    with open(os.path.join(DEMO_DIR, "DEMO_MODE.flag"), "w", encoding="utf-8") as f:
        f.write("SHAKTIX_COMMERCIAL_DEMO_ENABLED=1\nTIMESTAMP=" + datetime.now().isoformat())

    print("[SHAKTIX DEMO] 250 leads & 12 campaigns successfully injected into database!")

if __name__ == "__main__":
    seed_demo_data()
