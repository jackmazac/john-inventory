#!/usr/bin/env python3
"""Script to upload Excel file to the import endpoint."""
import requests
import sys
from pathlib import Path

def upload_excel_file(file_path: str):
    """Upload Excel file to the import endpoint."""
    url = "http://localhost:8000/import/upload"
    
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"Error: File not found: {file_path}")
        return False
    
    print(f"Uploading {file_path_obj.name}...")
    
    try:
        with open(file_path_obj, 'rb') as f:
            files = {'file': (file_path_obj.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            print("✓ File uploaded successfully!")
            print(f"Response URL: {response.url}")
            print("\nThe browser should now show the column mapping page.")
            return True
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure the server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    # Default to the Excel file in the project root
    default_file = Path(__file__).parent / "WJBK Computer invetory list 2025.xlsx"
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = str(default_file)
    
    upload_excel_file(file_path)
