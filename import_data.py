#!/usr/bin/env python3
"""Script to import Excel file data into the database."""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"
FILE_NAME = "WJBK Computer invetory list 2025.xlsx"

def import_excel_data():
    """Import Excel file via web interface."""
    print("=" * 60)
    print("Importing Excel Data into Database")
    print("=" * 60)
    
    # Step 1: Upload file
    print("\n1. Uploading file...")
    file_path = Path(FILE_NAME)
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/import/upload",
            files={"file": (file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    
    if response.status_code != 200:
        print(f"✗ Upload failed: {response.status_code}")
        print(response.text[:500])
        return False
    
    print("✓ File uploaded successfully")
    
    # Extract file path from response (we need to parse HTML or use API)
    # Let's use the API instead for a cleaner flow
    print("\n2. Using API to upload and parse...")
    
    # Upload via API
    with open(file_path, "rb") as f:
        api_response = requests.post(
            f"{BASE_URL}/api/files/upload",
            files={"file": (file_path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    
    if api_response.status_code != 200:
        print(f"✗ API upload failed: {api_response.status_code}")
        return False
    
    api_data = api_response.json()
    filename = api_data["file"]["filename"]
    print(f"✓ File uploaded via API: {filename}")
    
    # Step 2: Parse with mapping
    print("\n3. Parsing file with column mapping...")
    mapping = {
        "asset_tag": "Computer Name",
        "department": "Department",
        "operating_system": "Operating System",
        "notes": "Notes"
    }
    
    parse_response = requests.post(
        f"{BASE_URL}/api/files/{filename}/parse",
        params={"mapping": json.dumps(mapping)}
    )
    
    if parse_response.status_code != 200:
        print(f"✗ Parse failed: {parse_response.status_code}")
        print(parse_response.text[:500])
        return False
    
    parse_data = parse_response.json()
    print(f"✓ Parsed {parse_data['total_rows']} rows")
    
    # Step 3: Import via web interface (we'll use a direct database import)
    print("\n4. Importing data into database...")
    
    # Use the import service directly
    from app.database import SessionLocal
    from app.services.import_service import commit_import
    
    db = SessionLocal()
    try:
        upload_path = Path(f"uploads/{filename}")
        if not upload_path.exists():
            print(f"✗ File not found at {upload_path}")
            return False
        
        import_record = commit_import(
            db=db,
            file_path=upload_path,
            filename=filename,
            column_mapping=mapping,
            transformed_data=parse_data["transformed_data"],
            uploaded_by="import_script"
        )
        
        print(f"✓ Import completed!")
        print(f"  Import ID: {import_record.id}")
        print(f"  Records created: {import_record.records_created}")
        print(f"  Records updated: {import_record.records_updated}")
        print(f"  Records failed: {import_record.records_failed}")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = import_excel_data()
    if success:
        print("\n" + "=" * 60)
        print("✓ Data import completed successfully!")
        print("=" * 60)
        print("\nView the data at:")
        print(f"  Dashboard: {BASE_URL}/")
        print(f"  Assets: {BASE_URL}/assets")
    else:
        print("\n" + "=" * 60)
        print("✗ Data import failed")
        print("=" * 60)
