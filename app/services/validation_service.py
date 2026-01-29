"""Validation service for import data."""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.services.asset_service import get_asset_by_tag


def validate_asset_row(row_data: Dict[str, Any], row_index: int, db: Session) -> List[Dict[str, Any]]:
    """Validate a single asset row and return list of errors."""
    errors = []
    
    # Required field: asset_tag or computer_name
    if not row_data.get("asset_tag") and not row_data.get("computer_name"):
        errors.append({
            "row": row_index + 1,
            "field": "asset_tag",
            "message": "Asset tag or computer name is required"
        })
    
    # Check for duplicate asset_tag
    if row_data.get("asset_tag"):
        existing = get_asset_by_tag(db, row_data["asset_tag"])
        if existing:
            errors.append({
                "row": row_index + 1,
                "field": "asset_tag",
                "message": f"Asset tag '{row_data['asset_tag']}' already exists"
            })
    
    # Validate status values
    valid_statuses = ["active", "retired", "in-repair", "lost", "unassigned"]
    if row_data.get("status") and row_data["status"] not in valid_statuses:
        errors.append({
            "row": row_index + 1,
            "field": "status",
            "message": f"Invalid status '{row_data['status']}'. Must be one of: {', '.join(valid_statuses)}"
        })
    
    return errors


def validate_import_data(transformed_data: List[Dict[str, Any]], db: Session) -> Dict[str, Any]:
    """Validate all imported rows and return validation results."""
    all_errors = []
    valid_rows = []
    
    for i, row in enumerate(transformed_data):
        errors = validate_asset_row(row, i, db)
        if errors:
            all_errors.extend(errors)
        else:
            valid_rows.append((i, row))
    
    return {
        "errors": all_errors,
        "valid_rows": valid_rows,
        "total_rows": len(transformed_data),
        "valid_count": len(valid_rows),
        "error_count": len(all_errors)
    }
