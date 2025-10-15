from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://apple:hadafian@localhost/finance_tracker")
    database_host: str = os.getenv("DB_HOST", "localhost")
    database_port: int = int(os.getenv("DB_PORT", "5432"))
    database_name: str = os.getenv("DB_NAME", "finance_tracker")
    database_user: str = os.getenv("DB_USER", "apple")
    database_password: str = os.getenv("DB_PASSWORD", "hadafian")
    db_pool_min: int = 5
    db_pool_max: int = 20
    
    # API
    api_title: str = "Financial Tracker API"
    api_version: str = "1.0.0"
    api_description: str = "Multi-account financial management system"
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    base_currency: str = "PKR"
    timezone: str = "Asia/Karachi"
    
    # File uploads
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: str = ".xlsx,.xls,.csv"
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored

# Global settings instance
settings = Settings()

# Debug database configuration
print(f"Environment: {settings.environment}")
print(f"Database URL: {settings.database_url}")

# Construct database URLs if not provided or if using Railway
if os.getenv("DATABASE_URL"):
    # Railway or other cloud provider
    settings.database_url = os.getenv("DATABASE_URL")
    print(f"Using Railway DATABASE_URL: {settings.database_url}")
    # Parse individual components from DATABASE_URL if needed
    if settings.database_url.startswith("postgresql://"):
        # Convert to psycopg format
        settings.database_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif not settings.database_url or settings.database_url == "postgresql+psycopg://username:password@localhost/finance_tracker":
    # Local development
    settings.database_url = f"postgresql+psycopg://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"
    print(f"Using local database: {settings.database_url}")

# For direct psycopg connection (without SQLAlchemy)
def get_direct_database_url():
    if os.getenv("DATABASE_URL"):
        # Use Railway's DATABASE_URL but convert to direct psycopg format
        db_url = os.getenv("DATABASE_URL")
        if db_url.startswith("postgresql://"):
            return db_url
        return db_url.replace("postgresql+psycopg://", "postgresql://", 1)
    return f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"
