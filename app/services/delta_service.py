"""Delta detection service for comparing imported data with existing assets."""
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.services.asset_service import get_asset_by_tag


def detect_deltas(transformed_data: List[Dict[str, Any]], db: Session) -> Dict[str, List[Dict[str, Any]]]:
    """Detect differences between imported data and existing assets.
    
    Returns:
        {
            "new": [...],      # Assets that don't exist
            "modified": [...], # Assets that exist but have changes
            "unchanged": [...], # Assets that exist and are identical
        }
    """
    new_assets = []
    modified_assets = []
    unchanged_assets = []
    
    # Load all existing assets keyed by asset_tag
    existing_assets = {}
    for asset in db.query(Asset).all():
        if asset.asset_tag:
            existing_assets[asset.asset_tag] = asset
    
    for row_data in transformed_data:
        asset_tag = row_data.get("asset_tag")
        
        if not asset_tag:
            # No asset tag, treat as new
            new_assets.append(row_data)
            continue
        
        existing = existing_assets.get(asset_tag)
        
        if not existing:
            # New asset
            new_assets.append(row_data)
        else:
            # Check for modifications
            changes = _compare_asset(existing, row_data)
            if changes:
                modified_assets.append({
                    "row_data": row_data,
                    "existing": existing,
                    "changes": changes
                })
            else:
                unchanged_assets.append(row_data)
    
    return {
        "new": new_assets,
        "modified": modified_assets,
        "unchanged": unchanged_assets
    }


def _compare_asset(existing: Asset, new_data: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
    """Compare existing asset with new data and return changes."""
    changes = {}
    
    # Fields to compare
    fields_to_compare = [
        "department", "assigned_user_name", "assigned_user_id",
        "status", "operating_system", "notes", "computer_name"
    ]
    
    for field in fields_to_compare:
        existing_value = getattr(existing, field, None)
        new_value = new_data.get(field)
        
        # Normalize None/empty values
        existing_value = existing_value if existing_value else None
        new_value = new_value if new_value else None
        
        if existing_value != new_value:
            changes[field] = (existing_value, new_value)
    
    return changes
