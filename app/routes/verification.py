"""Verification routes."""
from fastapi import APIRouter, Request, Depends, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.verification import VerificationCampaign, VerificationRecord
from app.models.asset import Asset
from app.services.asset_service import get_assets

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/verification", response_class=HTMLResponse)
async def verification_list(
    request: Request,
    db: Session = Depends(get_db)
):
    """Verification campaigns list."""
    campaigns = db.query(VerificationCampaign).order_by(VerificationCampaign.created_at.desc()).all()
    
    return templates.TemplateResponse(
        "verification/campaigns.html",
        {
            "request": request,
            "campaigns": campaigns
        }
    )


@router.get("/verification/campaigns/new", response_class=HTMLResponse)
async def new_campaign_page(request: Request):
    """New campaign page."""
    return templates.TemplateResponse("verification/new_campaign.html", {"request": request})


@router.post("/verification/campaigns")
async def create_campaign(
    request: Request,
    name: str = Form(...),
    department: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Create new verification campaign."""
    # Get assets for the campaign
    assets, _ = get_assets(
        db,
        skip=0,
        limit=10000,
        department=department if department else None,
        status="active"
    )
    
    campaign = VerificationCampaign(
        name=name,
        department=department if department else None,
        due_date=date.fromisoformat(due_date) if due_date else None,
        created_by="user",  # TODO: Get from session
        total_count=len(assets),
        status="active"
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    return RedirectResponse(url=f"/verification/campaigns/{campaign.id}", status_code=303)


@router.get("/verification/campaigns/{campaign_id}", response_class=HTMLResponse)
async def campaign_detail(
    request: Request,
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Campaign detail with asset list."""
    campaign = db.query(VerificationCampaign).filter(VerificationCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get assets for verification
    if campaign.department:
        assets, _ = get_assets(db, skip=0, limit=10000, department=campaign.department, status="active")
    else:
        assets, _ = get_assets(db, skip=0, limit=10000, status="active")
    
    # Get verification records
    verified_asset_ids = {
        vr.asset_id for vr in db.query(VerificationRecord).filter(
            VerificationRecord.campaign_id == campaign_id
        ).all()
    }
    
    return templates.TemplateResponse(
        "verification/campaign_detail.html",
        {
            "request": request,
            "campaign": campaign,
            "assets": assets,
            "verified_asset_ids": verified_asset_ids
        }
    )


@router.post("/verification/verify")
async def verify_assets(
    request: Request,
    campaign_id: int = Form(...),
    verified_by: str = Form("user"),  # TODO: Get from session
    db: Session = Depends(get_db)
):
    # Get asset_ids from form (multiple values)
    form_data = await request.form()
    asset_ids = [int(id) for id in form_data.getlist("asset_ids")]
    """Mark assets as verified."""
    campaign = db.query(VerificationCampaign).filter(VerificationCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    for asset_id in asset_ids:
        # Check if already verified
        existing = db.query(VerificationRecord).filter(
            VerificationRecord.campaign_id == campaign_id,
            VerificationRecord.asset_id == asset_id
        ).first()
        
        if not existing:
            record = VerificationRecord(
                campaign_id=campaign_id,
                asset_id=asset_id,
                verified_by=verified_by,
                verified_status="verified"
            )
            db.add(record)
            
            # Update asset last_verified
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if asset:
                from datetime import datetime
                asset.last_verified_at = datetime.now()
                asset.last_verified_by = verified_by
    
    # Update campaign verified count
    campaign.verified_count = db.query(VerificationRecord).filter(
        VerificationRecord.campaign_id == campaign_id
    ).count()
    
    db.commit()
    
    return RedirectResponse(url=f"/verification/campaigns/{campaign_id}", status_code=303)


@router.get("/verification/reports/{campaign_id}")
async def verification_report(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Export verification report."""
    # TODO: Implement report export
    raise HTTPException(status_code=501, detail="Not implemented yet")
