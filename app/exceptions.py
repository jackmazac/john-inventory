"""Custom exceptions and error handlers."""
from fastapi import Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
import traceback
import logging
from app.config import settings

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="app/templates")


class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    errors = exc.errors()
    error_messages = [f"{err['loc']}: {err['msg']}" for err in errors]
    
    # Check if request expects HTML
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "errors/error.html",
            {
                "request": request,
                "status_code": 400,
                "error": "Validation Error",
                "message": "; ".join(error_messages),
                "details": errors
            },
            status_code=400
        )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "ValidationError",
            "message": "Invalid request data",
            "details": errors
        }
    )


async def http_exception_handler(request: Request, exc):
    """Handle HTTP exceptions."""
    # Check if request expects HTML
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "errors/error.html",
            {
                "request": request,
                "status_code": exc.status_code,
                "error": exc.detail if hasattr(exc, 'detail') else "Error",
                "message": exc.detail if hasattr(exc, 'detail') else str(exc)
            },
            status_code=exc.status_code
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail if hasattr(exc, 'detail') else str(exc),
            "status_code": exc.status_code
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Log full traceback
    error_traceback = traceback.format_exc()
    logger.error(f"Traceback: {error_traceback}")
    
    # Check if request expects HTML
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            "errors/error.html",
            {
                "request": request,
                "status_code": 500,
                "error": "Internal Server Error",
                "message": str(exc) if settings.debug else "An unexpected error occurred",
                "traceback": error_traceback if settings.debug else None
            },
            status_code=500
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
            "status_code": 500
        }
    )
