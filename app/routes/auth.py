"""
Authentication routes for the JDauth FastAPI application.

This module contains all authentication-related API endpoints including
user registration, login, and token refresh functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers.auth_controller import AuthController
from app.schemas.user import UserCreate
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.dependencies import get_current_user
from app.models.user import User

# Create router instance
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Initialize controller
auth_controller = AuthController()

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    summary="Register a new user",
    description="Create a new user account with username and password"
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data (username, password)
        db: Database session dependency
        
    Returns:
        Success message with user ID
        
    Raises:
        HTTPException: 400 if username already exists or validation fails
        HTTPException: 500 if internal server error occurs
    """
    try:
        result = auth_controller.register_user(db, user_data)
        return result
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and return JWT access token"
)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    Args:
        credentials: User login credentials (username, password)
        db: Database session dependency
        
    Returns:
        JWT token response with access token, token type, and expiration
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 422 if request validation fails
        HTTPException: 500 if internal server error occurs
    """
    try:
        token_response = auth_controller.login_user(db, credentials)
        return token_response
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to server error"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Generate a new access token using the current valid token"
)
def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    Refresh the current access token.
    
    Args:
        current_user: Current authenticated user (from token)
        db: Database session dependency
        token: Current JWT token from Authorization header
        
    Returns:
        New JWT token response
        
    Raises:
        HTTPException: 401 if token is invalid or expired
        HTTPException: 500 if internal server error occurs
    """
    try:
        new_token_response = auth_controller.refresh_token(db, token)
        return new_token_response
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed due to server error"
        )


# Health check endpoint for auth routes
@router.get(
    "/health",
    summary="Auth service health check",
    description="Check if authentication service is operational"
)
def auth_health_check():
    """
    Health check endpoint for authentication service.
    
    Returns:
        Service status information
    """
    return {
        "service": "authentication",
        "status": "healthy",
        "endpoints": [
            "/auth/register",
            "/auth/login",
            "/auth/refresh"
        ]
    }
