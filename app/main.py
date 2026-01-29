"""Main FastAPI application."""
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
import logging
from app.config import settings
from app.database import engine, Base
from app import models  # noqa: F401 - Import models to register them
from app.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables (for development - use Alembic in production)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

app = FastAPI(
    title="Fox Hardware Inventory",
    description="Hardware inventory management system",
    version="0.1.0",
    debug=settings.debug,
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")


# Root endpoint handled by dashboard router


# Include routers
from app.routes import auth, dashboard, assets, reports, verification, file_api
from app.middleware import UserContextMiddleware
import importlib
import_router = importlib.import_module("app.routes.import")

# Add user context middleware
app.add_middleware(UserContextMiddleware)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(assets.router)
app.include_router(import_router.router)
app.include_router(reports.router)
app.include_router(verification.router)
app.include_router(file_api.router)

# Help route
@app.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """Help page."""
    return templates.TemplateResponse("help/index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )
