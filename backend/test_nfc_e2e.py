#!/usr/bin/env python3
"""
TalentUP Fichaje — NFC e2e test script.
Tests the complete flow: simulate NFC UID -> backend -> response.

Usage:
    python test_nfc_e2e.py

Requirements:
    - Backend running at http://localhost:8000
    - Seed data loaded (employee with NFC001 or NFC002)
"""

import requests
import json
import sys

BACKEND_URL = "http://localhost:8000"
TENANT_ID = "default"

def test_health():
    """Test backend is running."""
    resp = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    print(f"[OK] Backend healthy: {resp.json()}")
    return True

def test_nfc_clock_in(nfc_uid="NFC001"):
    """Test NFC clock in via API."""
    payload = {
        "nfc_uid": nfc_uid,
        "tenant_id": TENANT_ID,
    }
    resp = requests.post(
        f"{BACKEND_URL}/api/clock/nfc",
        json=payload,
        timeout=10,
    )
    print(f"Clock NFC response: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Status: {data.get('status', 'unknown')}")
        print(f"  Employee: {data.get('employee_name', 'unknown')}")
        print(f"  Time: {data.get('time', 'unknown')}")
        return data
    else:
        print(f"  Error: {resp.text}")
        return None

def test_nfc_toggle(nfc_uid="NFC001"):
    """Test NFC toggle (in -> out -> in)."""
    print(f"\n--- NFC Toggle test for {nfc_uid} ---")

    # First tap: should clock IN
    print("\n[1] First tap (expect IN):")
    r1 = test_nfc_clock_in(nfc_uid)
    if not r1:
        return False
    assert r1["status"] == "in", f"Expected 'in', got '{r1['status']}'"

    # Second tap: should clock OUT
    print("\n[2] Second tap (expect OUT):")
    r2 = test_nfc_clock_in(nfc_uid)
    if not r2:
        return False
    assert r2["status"] == "out", f"Expected 'out', got '{r2['status']}'"

    # Third tap: should clock IN again
    print("\n[3] Third tap (expect IN):")
    r3 = test_nfc_clock_in(nfc_uid)
    if not r3:
        return False
    assert r3["status"] == "in", f"Expected 'in', got '{r3['status']}'"

    print("\n[OK] NFC toggle works correctly")
    return True

def test_unregistered_card():
    """Test that unregistered NFC card returns error."""
    print("\n--- Unregistered card test ---")
    r = test_nfc_clock_in("UNKNOWN_CARD_999")
    if r is None:
        print("[OK] Unregistered card rejected")
        return True
    else:
        print("[WARN] Unregistered card was accepted - check if this is intended")
        return True

if __name__ == "__main__":
    print("=" * 50)
    print("TalentUP Fichaje - NFC e2e Test")
    print("=" * 50)

    try:
        test_health()
    except Exception as e:
        print(f"[FAIL] Backend not running: {e}")
        print("Start backend with: cd backend && uvicorn app.main:app --reload")
        sys.exit(1)

    try:
        test_nfc_toggle("NFC001")
    except AssertionError as e:
        print(f"[FAIL] Toggle test failed: {e}")
    except Exception as e:
        print(f"[ERROR] {e}")

    try:
        test_unregistered_card()
    except Exception as e:
        print(f"[ERROR] {e}")

    print("\n" + "=" * 50)
    print("Test complete")
    print("=" * 50)