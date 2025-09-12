"""
FastAPI dependencies for JDauth application.

This module contains reusable FastAPI dependencies for authentication,
database sessions, and authorization.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.user import User
from app.utils.security import (
    SECRET_KEY,
    ALGORITHM,
    oauth2_scheme,
    get_user_by_username
)


def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user from JWT token.
    
    Args:
        token: JWT token from OAuth2 scheme
        db: Database session dependency
        
    Returns:
        User: The authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get the current active user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User: The active user
        
    Raises:
        HTTPException: If user is inactive
    """
    # Note: Add is_active field to User model if needed
    # For now, assume all users are active
    if hasattr(current_user, 'is_active') and not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    FastAPI dependency to require admin privileges.
    
    Args:
        current_user: Current active user from get_current_active_user dependency
        
    Returns:
        User: The admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    # Note: Add is_admin or role field to User model if needed
    # For now, assume all users can access admin features
    # This is a placeholder implementation
    if hasattr(current_user, 'is_admin') and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return current_user


def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    FastAPI dependency to get the current user if token is provided,
    otherwise return None. Useful for optional authentication.
    
    Args:
        token: Optional JWT token from OAuth2 scheme
        db: Database session dependency
        
    Returns:
        Optional[User]: The authenticated user if token is valid, None otherwise
    """
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = get_user_by_username(db, username=username)
    return user