"""
Test Suite for Next-Gen Advance Features:
1. AI Message Enhancer & Natural Spintax Generation
2. Sector-Specific High-Converting Templates (Coaching, Real Estate, Retail)
3. 2-Way Inbound Auto-Responder & HOT LEAD Auto-Tagging
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.db import init_db, get_connection
from core.crm import add_or_update_contact
from core.ai_enhancer import (
    generate_smart_spintax, get_template, list_industry_categories,
    INDUSTRY_TEMPLATES
)
from core.auto_responder import (
    init_auto_responder_table, get_all_rules, add_rule, delete_rule,
    process_incoming_message
)
from core.campaign_engine import parse_spintax

def test_ai_enhancer():
    print("[1/3] Testing AI Message Enhancer & Spintax Engine...")
    categories = list_industry_categories()
    assert len(categories) >= 4, f"Expected at least 4 industry templates, found {len(categories)}"
    print(f"      [OK] Industry Categories Loaded: {categories}")

    # Test template fetching
    coaching_tpl = get_template("Coaching & Education")
    assert "Admissions" in coaching_tpl or "NEET" in coaching_tpl
    print("      [OK] Coaching template loaded.")

    re_tpl = get_template("Real Estate & Plots")
    assert "Plot" in re_tpl or "Flat" in re_tpl or "Investment" in re_tpl or "Site" in re_tpl
    print("      [OK] Real Estate template loaded.")

    # Test Spintax conversion
    raw_msg = "Hello dear customer, we have a special offer for you with a big discount. Contact us today for details!"
    spintax = generate_smart_spintax(raw_msg)
    assert "{" in spintax and "|" in spintax and "}" in spintax
    print(f"      [OK] Converted to Spintax: {spintax[:60]}...")

    # Test evaluated spintax
    sample1 = parse_spintax(spintax)
    assert len(sample1) > 10
    print(f"      [OK] Sample Evaluated Message: '{sample1[:60]}...'")

def test_auto_responder():
    print("[2/3] Testing 2-Way Auto-Responder & Inbound Lead Tagger...")
    init_auto_responder_table()
    rules = get_all_rules()
    assert len(rules) >= 4, f"Expected at least 4 default rules, found {len(rules)}"
    print(f"      [OK] Active Auto-Reply Rules: {len(rules)}")

    # Add a test contact
    test_phone = "+919876599999"
    add_or_update_contact("Amit Sharma", test_phone, city="Patna", category="Student", tags="New Inquiry")

    # Test 1: Inbound "What is the price?"
    matched, reply, tag, _ = process_incoming_message(test_phone, "Bhaiya coaching ka price aur fees kya hai?")
    assert matched is True
    assert "pricing" in reply.lower() or "price" in reply.lower() or "fees" in reply.lower()
    print("      [OK] Price inquiry matched and auto-reply triggered!")

    # Test 2: Inbound "I am very interested, please call me"
    matched, reply, tag, _ = process_incoming_message(test_phone, "Sir I am interested, please call me for demo class")
    assert matched is True
    assert tag == "HOT_LEAD"
    print("      [OK] High-intent 'interested' inquiry matched -> Tagged as HOT_LEAD!")

    # Verify contact was updated in database with HOT_LEAD tag
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, tags FROM contacts WHERE phone LIKE '%9876599999%'")
        row = cursor.fetchone()
        assert row is not None
        assert "HOT_LEAD" in row["tags"] or row["status"] == "HOT LEAD"
        print(f"      [OK] Contact verified in CRM: Status='{row['status']}', Tags='{row['tags']}'")

def test_custom_rule_lifecycle():
    print("[3/3] Testing Custom Rule Addition & Deletion...")
    rule_id = add_rule("coupon, promo, discount code", "Use code DIWALI2026 for flat 20% off!", tag_lead="DISCOUNT_HUNTER")
    assert rule_id is not None

    matched, reply, tag, _ = process_incoming_message("+919876599999", "Do you have any discount code or coupon?")
    assert matched is True
    assert "DIWALI2026" in reply
    print("      [OK] Custom promotional rule triggered successfully!")

    delete_rule(rule_id)
    matched, _, _, _ = process_incoming_message("+919876599999", "Do you have any discount code or coupon?")
    assert matched is False
    print("      [OK] Custom rule deleted successfully.")

if __name__ == "__main__":
    print("=" * 65)
    print("RUNNING NEXT-GEN ADVANCE FEATURES TEST SUITE")
    print("=" * 65)
    init_db()
    test_ai_enhancer()
    test_auto_responder()
    test_custom_rule_lifecycle()
    print("=" * 65)
    print("ALL ADVANCE FEATURES TESTS PASSED 100%!")
    print("=" * 65)
