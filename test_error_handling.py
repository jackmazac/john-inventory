#!/usr/bin/env python3
"""Test error handling and hot reload."""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_error_scenarios():
    """Test various error scenarios."""
    print("=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    # Test 1: Invalid file type upload
    print("\n1. Testing invalid file type upload...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/files/upload",
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Non-existent file info
    print("\n2. Testing non-existent file info...")
    try:
        response = requests.get(f"{BASE_URL}/api/files/nonexistent.xlsx/info")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Invalid asset ID
    print("\n3. Testing invalid asset ID...")
    try:
        response = requests.get(f"{BASE_URL}/assets/99999")
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   ✓ 404 error handled correctly")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Invalid JSON in parse
    print("\n4. Testing invalid JSON in parse...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/files/WJBK Computer invetory list 2025.xlsx/parse",
            params={"mapping": "invalid json"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("Error handling tests complete!")
    print("=" * 60)

def test_hot_reload():
    """Test that hot reload is working."""
    print("\n" + "=" * 60)
    print("Testing Hot Reload")
    print("=" * 60)
    print("\nServer should automatically reload when code changes.")
    print("Check server logs for 'Reloading...' messages when files change.")
    print("\nTo test:")
    print("1. Make a small change to app/main.py")
    print("2. Watch the server terminal for reload messages")
    print("3. The change should be reflected without restarting")

if __name__ == "__main__":
    test_error_scenarios()
    test_hot_reload()
