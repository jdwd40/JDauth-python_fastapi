from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database settings
    database_url: str = "postgresql://JD:K1ller1921@localhost:5432/jdauth_db"
    test_database_url: str = "postgresql://JD:K1ller1921@localhost:5432/jdauth_test_db"
    
    # Database connection settings
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    # Security settings
    secret_key: str = "your_secure_secret_key_here_change_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application settings
    app_name: str = "JDauth FastAPI"
    debug: bool = True  # Enable for testing
    
    # PostgreSQL admin settings for database creation
    postgres_admin_url: str = "postgresql://JD:K1ller1921@localhost:5432/postgres"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
