"""
Utilities package for JDauth FastAPI application.

This package contains common utilities and dependencies used throughout the application.
"""

from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    authenticate_user,
    pwd_context,
    oauth2_scheme,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

from .dependencies import (
    get_current_user,
    get_current_active_user,
    require_admin
)

__all__ = [
    # Security utilities
    "verify_password",
    "get_password_hash", 
    "create_access_token",
    "authenticate_user",
    "pwd_context",
    "oauth2_scheme",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    
    # FastAPI dependencies
    "get_current_user",
    "get_current_active_user", 
    "require_admin"
]