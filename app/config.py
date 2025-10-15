from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+psycopg://apple:hadafian@localhost/finance_tracker"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "finance_tracker"
    database_user: str = "apple"
    database_password: str = "hadafian"
    db_pool_min: int = 5
    db_pool_max: int = 20
    
    # API
    api_title: str = "Financial Tracker API"
    api_version: str = "1.0.0"
    api_description: str = "Multi-account financial management system"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    base_currency: str = "PKR"
    timezone: str = "Asia/Karachi"
    
    # File uploads
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: str = ".xlsx,.xls,.csv"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored

# Global settings instance
settings = Settings()

# Construct database URLs if not provided
if not settings.database_url or settings.database_url == "postgresql+psycopg://username:password@localhost/finance_tracker":
    settings.database_url = f"postgresql+psycopg://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"

# For direct psycopg connection (without SQLAlchemy)
def get_direct_database_url():
    return f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"
