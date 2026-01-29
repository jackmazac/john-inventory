"""Asset routes."""
from fastapi import APIRouter, Request, Depends, Query, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import pandas as pd
import io
from app.database import get_db
from app.models.asset import Asset
from app.services.asset_service import (
    get_assets,
    get_asset,
    create_asset,
    update_asset,
    delete_asset,
    bulk_update_assets,
    bulk_delete_assets
)
from app.services.import_service import get_last_import_info
from app.schemas.asset import AssetCreate, AssetUpdate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/assets", response_class=HTMLResponse)
async def assets_list(
    request: Request,
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort_by: str = Query("asset_tag"),
    order: str = Query("asc")
):
    """Asset list view."""
    skip = (page - 1) * per_page
    assets, total = get_assets(
        db,
        skip=skip,
        limit=per_page,
        search=search,
        status=status,
        department=department,
        sort_by=sort_by,
        order=order
    )
    
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    user = getattr(request.state, "user", {"username": "Guest", "role": "guest", "is_authenticated": False})
    last_import = get_last_import_info(db)
    
    return templates.TemplateResponse(
        "assets/list.html",
        {
            "request": request,
            "assets": assets,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "search": search or "",
            "status": status or "",
            "department": department or "",
            "sort_by": sort_by,
            "order": order,
            "user": user,
            "last_import": last_import
        }
    )


@router.get("/assets/{asset_id}", response_class=HTMLResponse)
async def asset_detail(
    request: Request,
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Asset detail view."""
    asset = get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return templates.TemplateResponse(
        "assets/detail.html",
        {
            "request": request,
            "asset": asset
        }
    )


@router.get("/assets/{asset_id}/edit-form", response_class=HTMLResponse)
async def asset_edit_form(
    request: Request,
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Get asset row in edit mode."""
    asset = get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return templates.TemplateResponse(
        "components/asset_row.html",
        {
            "request": request,
            "asset": asset,
            "edit_mode": True
        }
    )


@router.get("/assets/{asset_id}/row", response_class=HTMLResponse)
async def asset_row(
    request: Request,
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Get asset row in view mode."""
    asset = get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return templates.TemplateResponse(
        "components/asset_row.html",
        {
            "request": request,
            "asset": asset,
            "edit_mode": False
        }
    )


@router.post("/assets/{asset_id}/edit", response_class=HTMLResponse)
async def asset_edit(
    request: Request,
    asset_id: int,
    db: Session = Depends(get_db),
    department: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    assigned_user_name: Optional[str] = Form(None),
    notes: Optional[str] = Form(None)
):
    """Save asset edits (requires explicit save)."""
    asset_update = AssetUpdate(
        department=department,
        status=status,
        assigned_user_name=assigned_user_name,
        notes=notes
    )
    
    updated_asset = update_asset(db, asset_id, asset_update, changed_by="user")
    if not updated_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Return updated row in view mode
    return templates.TemplateResponse(
        "components/asset_row.html",
        {
            "request": request,
            "asset": updated_asset,
            "edit_mode": False
        }
    )


@router.delete("/assets/{asset_id}")
async def asset_delete(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Delete asset (soft delete)."""
    success = delete_asset(db, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return RedirectResponse(url="/assets", status_code=303)


@router.post("/assets/{asset_id}/restore")
async def asset_restore(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Restore a retired asset."""
    asset = get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if asset.status != "retired":
        raise HTTPException(status_code=400, detail="Asset is not retired")
    
    asset_update = AssetUpdate(status="active")
    updated_asset = update_asset(db, asset_id, asset_update, changed_by="user")
    
    return RedirectResponse(url="/assets", status_code=303)


@router.post("/assets/bulk-update")
async def bulk_update(
    request: Request,
    db: Session = Depends(get_db),
    asset_ids: str = Form(...),
    status: Optional[str] = Form(None),
    department: Optional[str] = Form(None)
):
    """Bulk update assets."""
    try:
        ids = json.loads(asset_ids)
        ids = [int(id) for id in ids]
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid asset IDs")
    
    success = bulk_update_assets(db, ids, status=status, department=department)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update assets")
    
    return RedirectResponse(url="/assets", status_code=303)


@router.post("/assets/bulk-delete")
async def bulk_delete(
    request: Request,
    db: Session = Depends(get_db),
    asset_ids: str = Form(...)
):
    """Bulk delete assets."""
    try:
        ids = json.loads(asset_ids)
        ids = [int(id) for id in ids]
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid asset IDs")
    
    success = bulk_delete_assets(db, ids)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete assets")
    
    return RedirectResponse(url="/assets", status_code=303)


@router.get("/assets/export-selected")
async def export_selected(
    db: Session = Depends(get_db),
    selected_ids: str = Query(...)
):
    """Export selected assets."""
    try:
        ids = [int(id) for id in selected_ids.split(',')]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset IDs")
    
    assets = db.query(Asset).filter(Asset.id.in_(ids)).all()
    
    data = []
    for asset in assets:
        data.append({
            "Asset Tag": asset.asset_tag,
            "Computer Name": asset.computer_name,
            "Department": asset.department,
            "Assigned To": asset.assigned_user_name,
            "Status": asset.status,
            "Device Type": asset.device_type,
            "Operating System": asset.operating_system,
            "Serial Number": asset.serial_number,
            "Refresh Due Date": asset.refresh_due_date,
            "Last Verified": asset.last_verified_at,
        })
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=selected_assets_export.xlsx"}
    )
