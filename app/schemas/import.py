"""Import schemas."""
from pydantic import BaseModel
from typing import Dict, Optional, List, Any


class ColumnMappingRequest(BaseModel):
    """Column mapping configuration."""
    mapping: Dict[str, Optional[str]]  # target_field -> source_column


class ImportPreviewResponse(BaseModel):
    """Import preview response."""
    total_rows: int
    transformed_data: List[Dict[str, Any]]
    validation_errors: List[Dict[str, Any]]
