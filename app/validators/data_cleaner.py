"""Data normalization and cleaning functions."""
import re
import pandas as pd
from typing import Optional, Dict


def normalize_department(dept: Optional[str]) -> Optional[str]:
    """Normalize department name (case-insensitive, standardize to uppercase)."""
    if not dept or pd.isna(dept):
        return None
    
    dept_str = str(dept).strip()
    if not dept_str:
        return None
    
    # Normalize common variations
    dept_upper = dept_str.upper()
    
    # Handle case-insensitive matching for known departments
    department_map = {
        "IT": "IT",
        "NEWS": "NEWS",
        "SALES": "SALES",
        "ENG": "ENG",
        "ENGINEERING": "ENG",
        "WEATHER": "WEATHER",
        "SPORTS": "SPORTS",
        "CREATIVE SERVICES": "CREATIVE SERVICES",
        "CREATIVE": "CREATIVE SERVICES",
        "ACCOUNTING": "ACCOUNTING",
        "FINANCE": "FINANCE",
    }
    
    # Try exact match first
    if dept_upper in department_map:
        return department_map[dept_upper]
    
    # Try case-insensitive match
    for key, value in department_map.items():
        if dept_upper == key.upper():
            return value
    
    # Return uppercase version if no mapping found
    return dept_upper


def parse_notes(notes: Optional[str]) -> Dict[str, Optional[str]]:
    """Parse Notes field to extract user name and secondary asset tag.
    
    Expected format: "Name - AssetTag" or just "Name"
    """
    if not notes or pd.isna(notes):
        return {"user_name": None, "secondary_tag": None}
    
    notes_str = str(notes).strip()
    if not notes_str:
        return {"user_name": None, "secondary_tag": None}
    
    # Pattern: "Name - Tag" or "Name - Tag - Extra"
    parts = notes_str.split(" - ", 1)
    
    if len(parts) == 2:
        user_name = parts[0].strip()
        secondary_tag = parts[1].strip()
        return {"user_name": user_name, "secondary_tag": secondary_tag}
    else:
        # If no " - " separator, assume it's just a name
        return {"user_name": notes_str, "secondary_tag": None}


def clean_asset_tag(asset_tag: Optional[str]) -> Optional[str]:
    """Clean and validate asset tag format."""
    if not asset_tag or pd.isna(asset_tag):
        return None
    
    tag_str = str(asset_tag).strip()
    if not tag_str:
        return None
    
    # Remove any whitespace
    return tag_str.upper()


def normalize_status(status: Optional[str]) -> str:
    """Normalize status value."""
    if not status or pd.isna(status):
        return "active"
    
    status_str = str(status).strip().lower()
    
    status_map = {
        "active": "active",
        "inactive": "retired",
        "retired": "retired",
        "in-repair": "in-repair",
        "repair": "in-repair",
        "lost": "lost",
        "unassigned": "unassigned",
    }
    
    return status_map.get(status_str, "active")
