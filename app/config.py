"""Application configuration."""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./inventory.db"
    
    # Application
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = True
    
    # Uploads
    upload_dir: Path = Path("uploads")
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    
    # Session
    session_secret: str = "dev-session-secret-change-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Ensure upload directory exists
settings.upload_dir.mkdir(parents=True, exist_ok=True)
