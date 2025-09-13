"""
Auth Controller for handling authentication business logic.

This controller orchestrates authentication operations by coordinating
between auth and user services, handling validation, and managing
business rules for registration, login, and token refresh.
"""

from datetime import timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import auth_service, user_service
from app.schemas.user import UserCreate
from app.schemas.auth import LoginRequest, TokenResponse
from app.config.settings import settings


class AuthController:
    """Controller for authentication-related business logic."""

    def register_user(self, db: Session, user_data: UserCreate) -> Dict[str, Any]:
        """
        Register a new user with business rule validation.
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            Registration success response with user ID
            
        Raises:
            HTTPException: If registration fails due to validation or business rules
        """
        try:
            # Create user through service layer
            new_user = user_service.create_user(db, user_data)
            
            return {
                "message": "User created successfully",
                "user_id": new_user.id
            }
            
        except ValueError as e:
            # Handle business rule violations
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            # Handle unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    def login_user(self, db: Session, credentials: LoginRequest, ip_address: str = None) -> TokenResponse:
        """
        Authenticate user and generate access token.
        
        Args:
            db: Database session
            credentials: User login credentials
            ip_address: IP address of the login attempt (for security tracking)
            
        Returns:
            JWT token response
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Authenticate user with IP tracking
            user = auth_service.authenticate_user(
                db, credentials.username, credentials.password, ip_address
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            access_token = auth_service.create_access_token(
                data={"sub": user.username}, 
                expires_delta=access_token_expires
            )
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=settings.access_token_expire_minutes * 60  # Convert to seconds
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    def refresh_token(self, db: Session, token: str) -> TokenResponse:
        """
        Refresh an existing JWT token.
        
        Args:
            db: Database session
            token: Current JWT token
            
        Returns:
            New JWT token response
            
        Raises:
            HTTPException: If token refresh fails
        """
        try:
            # Get user from current token
            user = auth_service.get_current_user_from_token(db, token)
            
            # Create new access token
            access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
            new_access_token = auth_service.create_access_token(
                data={"sub": user.username}, 
                expires_delta=access_token_expires
            )
            
            return TokenResponse(
                access_token=new_access_token,
                token_type="bearer",
                expires_in=settings.access_token_expire_minutes * 60  # Convert to seconds
            )
            
        except ValueError as e:
            # Handle token validation errors
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        except Exception as e:
            # Handle unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
