"""FastAPI dependencies."""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.config import settings

security = HTTPBasic()


def get_current_user(request: Request) -> dict:
    """Get current user from session cookie."""
    # For MVP, get username from session cookie
    # In production, implement proper user authentication
    username = request.cookies.get("session", "Guest")
    role = "admin" if username != "Guest" else "guest"  # Simplified role assignment
    
    return {
        "username": username,
        "role": role,
        "is_authenticated": username != "Guest"
    }


def get_db_session(db: Session = Depends(get_db)):
    """Get database session."""
    return db
