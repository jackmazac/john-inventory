"""Asset service for CRUD operations."""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate


def get_asset(db: Session, asset_id: int) -> Optional[Asset]:
    """Get asset by ID."""
    return db.query(Asset).filter(Asset.id == asset_id).first()


def get_asset_by_tag(db: Session, asset_tag: str) -> Optional[Asset]:
    """Get asset by asset tag."""
    return db.query(Asset).filter(Asset.asset_tag == asset_tag).first()


def get_assets(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    sort_by: str = "asset_tag",
    order: str = "asc"
) -> tuple[List[Asset], int]:
    """Get assets with filtering and pagination."""
    query = db.query(Asset)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Asset.asset_tag.ilike(search_term),
                Asset.computer_name.ilike(search_term),
                Asset.assigned_user_name.ilike(search_term),
                Asset.serial_number.ilike(search_term),
                Asset.department.ilike(search_term)
            )
        )
    
    if status:
        query = query.filter(Asset.status == status)
    
    if department:
        query = query.filter(Asset.department == department)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Asset, sort_by, Asset.asset_tag)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    assets = query.offset(skip).limit(limit).all()
    
    return assets, total


def create_asset(db: Session, asset: AssetCreate) -> Asset:
    """Create a new asset."""
    db_asset = Asset(**asset.model_dump())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


def update_asset(db: Session, asset_id: int, asset_update: AssetUpdate, changed_by: str = "system") -> Optional[Asset]:
    """Update an asset."""
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    
    update_data = asset_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_value = getattr(db_asset, field)
        if old_value != value:
            setattr(db_asset, field, value)
            # TODO: Create history record in Phase 4
    
    db_asset.updated_at = datetime.now()
    db.commit()
    db.refresh(db_asset)
    return db_asset


def delete_asset(db: Session, asset_id: int) -> bool:
    """Soft delete an asset (set status to retired)."""
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return False
    
    db_asset.status = "retired"
    db_asset.updated_at = datetime.now()
    db.commit()
    return True


def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Get dashboard statistics."""
    total = db.query(Asset).count()
    active = db.query(Asset).filter(Asset.status == "active").count()
    unassigned = db.query(Asset).filter(
        or_(
            Asset.assigned_user_name.is_(None),
            Asset.assigned_user_name == "",
            Asset.status == "unassigned"
        )
    ).count()
    
    # Assets due for refresh in next 90 days
    today = date.today()
    due_date = today + timedelta(days=90)
    due_for_refresh = db.query(Asset).filter(
        Asset.refresh_due_date.isnot(None),
        Asset.refresh_due_date <= due_date,
        Asset.status == "active"
    ).count()
    
    # Calculate trends (compare to 30 days ago)
    # For MVP, we'll use a simple approach - in production, store historical snapshots
    # For now, return 0 trends (no historical data available)
    total_trend = 0
    active_trend = 0
    
    return {
        "total": total,
        "active": active,
        "unassigned": unassigned,
        "due_for_refresh": due_for_refresh,
        "total_trend": total_trend,
        "active_trend": active_trend
    }


def get_recent_activity(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent import and edit activity."""
    from app.models.import_record import ImportRecord
    from app.models.asset_history import AssetHistory
    
    activities = []
    
    # Get recent imports
    imports = db.query(ImportRecord).order_by(ImportRecord.uploaded_at.desc()).limit(limit).all()
    for imp in imports:
        activities.append({
            "type": "import",
            "timestamp": imp.uploaded_at,
            "description": f"Imported {imp.records_processed} records from {imp.filename}",
            "status": imp.status
        })
    
    # Get recent edits (from history)
    edits = db.query(AssetHistory).order_by(AssetHistory.changed_at.desc()).limit(limit).all()
    for edit in edits:
        activities.append({
            "type": "edit",
            "timestamp": edit.changed_at,
            "description": f"Updated asset {edit.asset.asset_tag if edit.asset else 'N/A'}",
            "changed_by": edit.changed_by
        })
    
    # Sort by timestamp and return top N
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]


def get_department_counts(db: Session) -> Dict[str, int]:
    """Get asset counts by department."""
    results = db.query(
        Asset.department,
        func.count(Asset.id).label("count")
    ).filter(
        Asset.department.isnot(None),
        Asset.status == "active"
    ).group_by(Asset.department).all()
    
    return {dept: count for dept, count in results if dept}


def bulk_update_assets(db: Session, asset_ids: List[int], status: Optional[str] = None, department: Optional[str] = None) -> bool:
    """Bulk update multiple assets."""
    try:
        assets = db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
        for asset in assets:
            if status:
                asset.status = status
            if department:
                asset.department = department
            asset.updated_at = datetime.now()
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def bulk_delete_assets(db: Session, asset_ids: List[int]) -> bool:
    """Bulk delete (retire) multiple assets."""
    try:
        assets = db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
        for asset in assets:
            asset.status = "retired"
            asset.updated_at = datetime.now()
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
