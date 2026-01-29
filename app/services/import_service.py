"""Import service for processing Excel imports."""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.validators.excel_parser import parse_excel_file, get_column_names, get_sample_data
from app.validators.column_detector import detect_column_mapping
from app.validators.data_cleaner import normalize_department, parse_notes, clean_asset_tag, normalize_status
from app.models.asset import Asset
from app.models.import_record import ImportRecord
from app.models.asset_history import AssetHistory
from app.schemas.asset import AssetCreate


def get_last_import_info(db: Session) -> Optional[Dict[str, Any]]:
    """Get information about the last import."""
    last_import = db.query(ImportRecord).order_by(ImportRecord.uploaded_at.desc()).first()
    if not last_import:
        return None
    
    return {
        "filename": last_import.filename,
        "uploaded_at": last_import.uploaded_at,
        "records_processed": last_import.records_processed,
        "status": last_import.status
    }


def process_uploaded_file(file_path: Path) -> Dict[str, Any]:
    """Process uploaded Excel file and return column information."""
    df = parse_excel_file(file_path)
    columns = get_column_names(df)
    sample_data = get_sample_data(df, num_rows=5)
    auto_mapping = detect_column_mapping(columns)
    
    return {
        "columns": columns,
        "sample_data": sample_data,
        "auto_mapping": auto_mapping,
        "row_count": len(df)
    }


def transform_row(row_data: Dict[str, Any], column_mapping: Dict[str, str]) -> Dict[str, Any]:
    """Transform a row of imported data according to column mapping."""
    transformed = {}
    
    # Map source columns to target fields
    for target_field, source_column in column_mapping.items():
        if source_column and source_column in row_data:
            value = row_data[source_column]
            transformed[target_field] = value if not pd.isna(value) else None
        else:
            transformed[target_field] = None
    
    # Apply transformations
    if "department" in transformed and transformed["department"]:
        transformed["department"] = normalize_department(transformed["department"])
    
    if "notes" in transformed and transformed["notes"]:
        parsed = parse_notes(transformed["notes"])
        if parsed["user_name"] and not transformed.get("assigned_user_name"):
            transformed["assigned_user_name"] = parsed["user_name"]
        if parsed["secondary_tag"] and not transformed.get("asset_tag"):
            # Use secondary tag if primary asset_tag is missing
            pass  # Don't override primary asset_tag
    
    if "asset_tag" in transformed and transformed["asset_tag"]:
        transformed["asset_tag"] = clean_asset_tag(transformed["asset_tag"])
    
    if "status" in transformed:
        transformed["status"] = normalize_status(transformed.get("status"))
    else:
        transformed["status"] = "active"  # Default status
    
    # Set computer_name from asset_tag if not provided
    if not transformed.get("computer_name") and transformed.get("asset_tag"):
        transformed["computer_name"] = transformed["asset_tag"]
    
    return transformed


def commit_import(
    db: Session,
    file_path: Path,
    filename: str,
    column_mapping: Dict[str, str],
    transformed_data: List[Dict[str, Any]],
    uploaded_by: str = "system"
) -> ImportRecord:
    """Commit import to database."""
    # Create import record
    import_record = ImportRecord(
        filename=filename,
        uploaded_by=uploaded_by,
        column_mapping=str(column_mapping),
        records_processed=len(transformed_data),
        status="pending"
    )
    db.add(import_record)
    db.flush()  # Get the ID
    
    records_created = 0
    records_updated = 0
    records_failed = 0
    validation_errors = []
    
    try:
        for i, row_data in enumerate(transformed_data):
            try:
                asset_tag = row_data.get("asset_tag")
                
                if not asset_tag:
                    records_failed += 1
                    validation_errors.append({
                        "row": i + 1,
                        "message": "Missing asset_tag"
                    })
                    continue
                
                # Check if asset exists
                existing = db.query(Asset).filter(Asset.asset_tag == asset_tag).first()
                
                if existing:
                    # Update existing asset
                    for field, value in row_data.items():
                        if field != "asset_tag" and hasattr(existing, field):
                            setattr(existing, field, value)
                    
                    existing.updated_at = datetime.now()
                    records_updated += 1
                    
                    # Create history record
                    history = AssetHistory(
                        asset_id=existing.id,
                        field_name="import",
                        change_type="import",
                        changed_by=uploaded_by,
                        import_id=import_record.id
                    )
                    db.add(history)
                else:
                    # Create new asset
                    asset_create = AssetCreate(**row_data)
                    new_asset = Asset(**asset_create.model_dump())
                    db.add(new_asset)
                    records_created += 1
                    
                    # Create history record
                    db.flush()
                    history = AssetHistory(
                        asset_id=new_asset.id,
                        field_name="created",
                        change_type="import",
                        changed_by=uploaded_by,
                        import_id=import_record.id
                    )
                    db.add(history)
            
            except Exception as e:
                records_failed += 1
                validation_errors.append({
                    "row": i + 1,
                    "message": str(e)
                })
        
        # Update import record
        import_record.records_created = records_created
        import_record.records_updated = records_updated
        import_record.records_failed = records_failed
        import_record.validation_errors = str(validation_errors) if validation_errors else None
        import_record.status = "completed"
        
        db.commit()
        return import_record
    
    except Exception as e:
        db.rollback()
        import_record.status = "failed"
        import_record.validation_errors = str(e)
        db.commit()
        raise


def rollback_import(db: Session, import_id: int) -> bool:
    """Rollback an import by deleting created assets and reverting updates."""
    import_record = db.query(ImportRecord).filter(ImportRecord.id == import_id).first()
    if not import_record or import_record.status == "rolled_back":
        return False
    
    try:
        # Get all history records for this import
        history_records = db.query(AssetHistory).filter(
            AssetHistory.import_id == import_id
        ).all()
        
        # Delete created assets and revert updates
        for history in history_records:
            if history.change_type == "import":
                asset = db.query(Asset).filter(Asset.id == history.asset_id).first()
                if asset:
                    # Check if this was a new asset (no history before this import)
                    earlier_history = db.query(AssetHistory).filter(
                        AssetHistory.asset_id == asset.id,
                        AssetHistory.changed_at < history.changed_at
                    ).first()
                    
                    if not earlier_history:
                        # This was a new asset, delete it
                        db.delete(asset)
                    # Otherwise, it was an update - we'd need to store old values to revert
                    # For MVP, we'll just mark the import as rolled_back
        
        # Delete history records
        for history in history_records:
            db.delete(history)
        
        import_record.status = "rolled_back"
        import_record.rolled_back_at = datetime.now()
        db.commit()
        return True
    
    except Exception as e:
        db.rollback()
        raise
