#!/usr/bin/env python3
"""Test navigation links."""
import requests

BASE_URL = "http://localhost:8000"

def test_navigation():
    """Test all navigation endpoints."""
    print("=" * 60)
    print("Testing Navigation Links")
    print("=" * 60)
    
    endpoints = [
        ("/", "Dashboard"),
        ("/assets", "Assets"),
        ("/import", "Import"),
        ("/verification", "Verification"),
        ("/reports/refresh-schedule", "Reports"),
    ]
    
    for path, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{path}", allow_redirects=False)
            if response.status_code == 200:
                print(f"✓ {name:15} ({path:30}) - Status: {response.status_code}")
            elif response.status_code == 303 or response.status_code == 302:
                print(f"→ {name:15} ({path:30}) - Redirect: {response.status_code} -> {response.headers.get('Location', 'N/A')}")
            else:
                print(f"✗ {name:15} ({path:30}) - Status: {response.status_code}")
        except Exception as e:
            print(f"✗ {name:15} ({path:30}) - Error: {e}")

if __name__ == "__main__":
    test_navigation()
