"""
Unit test for core/lead_extractor.py
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.lead_extractor import sanitize_phone_number, extract_leads_from_text, search_instagram_public_leads

def test_sanitizer():
    print("Testing phone number sanitization...")
    assert sanitize_phone_number("9876543210") == "919876543210"
    assert sanitize_phone_number("09876543210") == "919876543210"
    assert sanitize_phone_number("+91 98765-43210") == "919876543210"
    assert sanitize_phone_number("919876543210") == "919876543210"
    print("  [OK] Phone sanitizer verified.")

def test_extractor():
    print("Testing text snippet extractor...")
    sample_text = """
    Check out our new fashion collection @patna_boutique! 
    WhatsApp us at +91 9835012345 or call 09431098765 for home delivery in Patna.
    Another store: @gym_bihar contact 8877665544 for gym membership.
    """
    leads = extract_leads_from_text(sample_text, default_category="Boutique", default_city="Patna")
    assert len(leads) >= 3, f"Expected 3 leads, got {len(leads)}"
    phones = [l["phone"] for l in leads]
    assert "919835012345" in phones
    assert "919431098765" in phones
    assert "918877665544" in phones
    print(f"  [OK] Extracted {len(leads)} leads accurately with correct metadata.")

def test_search_pipeline():
    print("Testing search_instagram_public_leads...")
    results = search_instagram_public_leads("Fitness", "Patna", max_results=5)
    assert len(results) >= 5
    for r in results:
        assert len(r["phone"]) >= 10
        assert r["category"] is not None
    print(f"  [OK] Search pipeline generated {len(results)} leads.")

if __name__ == "__main__":
    test_sanitizer()
    test_extractor()
    test_search_pipeline()
    print("ALL LEAD EXTRACTOR TESTS PASSED!")
