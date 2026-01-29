"""Dashboard routes."""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.asset_service import get_dashboard_stats, get_department_counts, get_recent_activity

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Dashboard page."""
    stats = get_dashboard_stats(db)
    dept_counts = get_department_counts(db)
    recent_activity = get_recent_activity(db, limit=5)
    user = getattr(request.state, "user", {"username": "Guest", "role": "guest", "is_authenticated": False})
    
    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "stats": stats,
            "dept_counts": dept_counts,
            "recent_activity": recent_activity,
            "user": user
        }
    )


@router.get("/api/stats", response_class=JSONResponse)
async def api_stats(db: Session = Depends(get_db)):
    """API endpoint for dashboard stats (for HTMX polling)."""
    stats = get_dashboard_stats(db)
    dept_counts = get_department_counts(db)
    return {
        "stats": stats,
        "dept_counts": dept_counts
    }
