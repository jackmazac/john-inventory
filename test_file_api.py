#!/usr/bin/env python3
"""Test script for Excel file management API."""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/files"
TEST_FILE = "WJBK Computer invetory list 2025.xlsx"

def test_upload():
    """Test file upload."""
    print("Testing file upload...")
    file_path = Path(TEST_FILE)
    
    if not file_path.exists():
        print(f"Error: Test file not found: {TEST_FILE}")
        return None
    
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            files={"file": (file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Upload successful!")
        print(f"  Filename: {data['file']['filename']}")
        print(f"  Rows: {data['file']['row_count']}")
        print(f"  Columns: {len(data['file']['columns'])}")
        return data['file']['filename']
    else:
        print(f"✗ Upload failed: {response.status_code}")
        print(f"  {response.text}")
        return None

def test_list():
    """Test listing files."""
    print("\nTesting file list...")
    response = requests.get(f"{BASE_URL}/list")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ List successful!")
        print(f"  Total files: {data['total_files']}")
        print(f"  Total imports: {data['total_imports']}")
        if data['files']:
            print(f"  Files: {[f['filename'] for f in data['files']]}")
        return data['files'][0]['filename'] if data['files'] else None
    else:
        print(f"✗ List failed: {response.status_code}")
        return None

def test_info(filename):
    """Test getting file info."""
    if not filename:
        return
    print(f"\nTesting file info for {filename}...")
    response = requests.get(f"{BASE_URL}/{filename}/info")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Info retrieval successful!")
        print(f"  Size: {data['size']} bytes")
        print(f"  Columns: {data['columns']}")
        print(f"  Row count: {data['row_count']}")
    else:
        print(f"✗ Info retrieval failed: {response.status_code}")

def test_columns(filename):
    """Test getting file columns."""
    if not filename:
        return
    print(f"\nTesting column info for {filename}...")
    response = requests.get(f"{BASE_URL}/{filename}/columns")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Column info successful!")
        print(f"  Columns: {data['columns']}")
        print(f"  Column count: {data['column_count']}")
    else:
        print(f"✗ Column info failed: {response.status_code}")

def test_parse(filename):
    """Test parsing file."""
    if not filename:
        return
    print(f"\nTesting file parsing for {filename}...")
    
    # Test with auto-mapping
    response = requests.post(f"{BASE_URL}/{filename}/parse")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Parse successful!")
        print(f"  Total rows: {data['total_rows']}")
        print(f"  Sample row: {data['transformed_data'][0] if data['transformed_data'] else 'None'}")
    else:
        print(f"✗ Parse failed: {response.status_code}")
        print(f"  {response.text}")

def test_export(filename):
    """Test exporting file."""
    if not filename:
        return
    print(f"\nTesting file export for {filename}...")
    
    # Export as JSON
    response = requests.get(f"{BASE_URL}/{filename}/export?format=json")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ JSON export successful!")
        print(f"  Rows exported: {data['row_count']}")
    else:
        print(f"✗ JSON export failed: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("Excel File Management API Test")
    print("=" * 60)
    
    # Test upload
    filename = test_upload()
    
    # Test list
    listed_filename = test_list()
    if not filename:
        filename = listed_filename
    
    # Test info
    test_info(filename)
    
    # Test columns
    test_columns(filename)
    
    # Test parse
    test_parse(filename)
    
    # Test export
    test_export(filename)
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)
    print(f"\nAPI Documentation: http://localhost:8000/docs")
    print(f"API Base URL: {BASE_URL}")
