"""Middleware for adding user context to requests."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.dependencies import get_current_user


class UserContextMiddleware(BaseHTTPMiddleware):
    """Add user context to request state."""
    
    async def dispatch(self, request: Request, call_next):
        # Add user context to request state
        try:
            user = get_current_user(request)
            request.state.user = user
        except Exception:
            # If user can't be determined, set default
            request.state.user = {
                "username": "Guest",
                "role": "guest",
                "is_authenticated": False
            }
        
        response = await call_next(request)
        return response
