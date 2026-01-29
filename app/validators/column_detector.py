"""Auto-detect column mappings."""
from typing import Dict, List, Optional


# Common field name patterns for auto-detection
FIELD_PATTERNS = {
    "asset_tag": ["asset tag", "asset_tag", "asset", "computer name", "computer_name", "tag", "id"],
    "computer_name": ["computer name", "computer_name", "name", "hostname"],
    "department": ["department", "dept", "division", "group"],
    "assigned_user_name": ["user", "username", "assigned to", "assigned_to", "user name", "user_name", "employee", "owner"],
    "assigned_user_id": ["user id", "user_id", "employee id", "employee_id", "userid"],
    "operating_system": ["os", "operating system", "operating_system", "platform"],
    "serial_number": ["serial", "serial number", "serial_number", "sn"],
    "status": ["status", "state"],
    "notes": ["notes", "note", "comments", "comment", "description"],
}


def detect_column_mapping(source_columns: List[str]) -> Dict[str, Optional[str]]:
    """Auto-detect column mappings from source column names."""
    mapping = {}
    source_lower = [col.lower().strip() for col in source_columns]
    
    for target_field, patterns in FIELD_PATTERNS.items():
        matched = None
        for pattern in patterns:
            for i, source_col in enumerate(source_lower):
                if pattern in source_col:
                    matched = source_columns[i]
                    break
            if matched:
                break
        mapping[target_field] = matched
    
    return mapping


def get_available_target_fields() -> List[str]:
    """Get list of available target fields for mapping."""
    return list(FIELD_PATTERNS.keys())
