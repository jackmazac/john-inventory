"""Report routes."""
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta
import pandas as pd
import io
from app.database import get_db
from app.services.asset_service import get_assets
from app.models.asset import Asset

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/reports/refresh-schedule", response_class=HTMLResponse)
async def refresh_schedule_report(
    request: Request,
    db: Session = Depends(get_db),
    days: int = Query(90, ge=1, le=365)
):
    """Refresh schedule report."""
    today = date.today()
    due_date = today + timedelta(days=days)
    
    assets = db.query(Asset).filter(
        Asset.refresh_due_date.isnot(None),
        Asset.refresh_due_date <= due_date,
        Asset.status == "active"
    ).order_by(Asset.refresh_due_date).all()
    
    return templates.TemplateResponse(
        "reports/refresh_schedule.html",
        {
            "request": request,
            "assets": assets,
            "days": days
        }
    )


@router.get("/reports/department-inventory", response_class=HTMLResponse)
async def department_inventory_report(
    request: Request,
    db: Session = Depends(get_db),
    department: Optional[str] = None
):
    """Department inventory report."""
    query = db.query(Asset).filter(Asset.status == "active")
    
    if department:
        query = query.filter(Asset.department == department)
    
    assets = query.order_by(Asset.department, Asset.asset_tag).all()
    
    # Group by department
    dept_groups = {}
    for asset in assets:
        dept = asset.department or "Unassigned"
        if dept not in dept_groups:
            dept_groups[dept] = []
        dept_groups[dept].append(asset)
    
    return templates.TemplateResponse(
        "reports/department_inventory.html",
        {
            "request": request,
            "dept_groups": dept_groups,
            "selected_dept": department
        }
    )


@router.get("/reports/unassigned", response_class=HTMLResponse)
async def unassigned_report(
    request: Request,
    db: Session = Depends(get_db)
):
    """Unassigned assets report."""
    assets = db.query(Asset).filter(
        Asset.status == "active",
        (Asset.assigned_user_name.is_(None) | (Asset.assigned_user_name == ""))
    ).order_by(Asset.department, Asset.asset_tag).all()
    
    return templates.TemplateResponse(
        "reports/unassigned.html",
        {
            "request": request,
            "assets": assets
        }
    )


@router.get("/assets/export")
async def export_assets(
    db: Session = Depends(get_db),
    format: str = Query("xlsx", pattern="^(xlsx|csv)$"),
    search: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None
):
    """Export assets to XLSX or CSV."""
    assets, _ = get_assets(db, skip=0, limit=10000, search=search, status=status, department=department)
    
    # Convert to DataFrame
    data = []
    for asset in assets:
        data.append({
            "Asset Tag": asset.asset_tag,
            "Computer Name": asset.computer_name,
            "Department": asset.department,
            "Assigned To": asset.assigned_user_name,
            "Status": asset.status,
            "Operating System": asset.operating_system,
            "Serial Number": asset.serial_number,
            "Purchase Date": asset.purchase_date,
            "Refresh Due Date": asset.refresh_due_date,
        })
    
    df = pd.DataFrame(data)
    
    if format == "xlsx":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=assets_export.xlsx"}
        )
    else:
        output = io.StringIO()
        df.to_csv(output, index=False)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=assets_export.csv"}
        )
