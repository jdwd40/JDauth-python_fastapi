"""
FastAPI dependencies for JDauth application.

This module contains reusable dependency functions for authentication,
authorization, and database session management.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.config.database import get_db
from app.config.settings import settings
from app.models.user import User
from app.services import user_service

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session dependency
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = user_service.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current authenticated and active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: 400 if user is inactive
    """
    # Check if user has an 'is_active' attribute
    if hasattr(current_user, 'is_active') and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require admin privileges for the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user (if admin)
        
    Raises:
        HTTPException: 403 if user is not an admin
    """
    # Check admin privileges
    if not _is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


def _is_admin_user(user: User) -> bool:
    """
    Check if a user has admin privileges.
    
    For now, this is a simple implementation.
    In a real application, this would check roles/permissions.
    
    Args:
        user: User to check
        
    Returns:
        True if user has admin privileges
    """
    # Simple implementation: check if user has is_admin attribute
    # or if username is 'admin' (for testing purposes)
    if hasattr(user, 'is_admin'):
        return getattr(user, 'is_admin', False)
    
    # Fallback: check username (temporary for testing)
    return user.username == 'admin'
