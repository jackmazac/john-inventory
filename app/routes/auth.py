"""Authentication routes."""
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Simple login - accepts any credentials for MVP."""
    # For MVP, accept any username/password
    # In production, implement proper authentication
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    # Set session cookie (simplified for MVP)
    response.set_cookie(key="session", value=username, httponly=True)
    return response


@router.post("/logout")
async def logout():
    """Logout."""
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="session")
    return response
