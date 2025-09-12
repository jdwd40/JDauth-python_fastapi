"""
User routes for the JDauth FastAPI application.

This module contains all user-related API endpoints including
profile management, protected routes, and user administration.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers.user_controller import UserController
from app.schemas.user import UserResponse, UserUpdate
from app.utils.dependencies import get_current_user
from app.models.user import User

# Create router instance
router = APIRouter(prefix="/user", tags=["User Management"])

# Initialize controller
user_controller = UserController()


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the profile information of the currently authenticated user"
)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's profile.
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        User profile information
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 500 if internal server error occurs
    """
    try:
        profile = user_controller.get_current_user_profile(current_user)
        return profile
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update user profile",
    description="Update the profile information of the currently authenticated user"
)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile.
    
    Args:
        update_data: Profile update data
        current_user: Current authenticated user from JWT token
        db: Database session dependency
        
    Returns:
        Updated user profile information
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 400 if validation fails
        HTTPException: 500 if internal server error occurs
    """
    try:
        updated_profile = user_controller.update_user_profile(db, current_user, update_data)
        return updated_profile
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get(
    "/protected",
    summary="Protected endpoint example",
    description="Example of a protected endpoint that requires authentication"
)
def protected_route(
    current_user: User = Depends(get_current_user)
):
    """
    Protected endpoint that requires authentication.
    
    This is an example endpoint to demonstrate authentication requirements.
    
    Args:
        current_user: Current authenticated user from JWT token
        
    Returns:
        Personalized message for the authenticated user
        
    Raises:
        HTTPException: 401 if user is not authenticated
    """
    return {
        "message": f"Hello, {current_user.username}! This is a protected endpoint.",
        "user_id": current_user.id,
        "access_level": "authenticated"
    }


# Admin-only routes (separate router for admin endpoints)
admin_router = APIRouter(tags=["User Administration"])


@admin_router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all users (Admin only)",
    description="Retrieve a paginated list of all users. Requires admin privileges."
)
def get_users_list(
    skip: int = Query(0, ge=0, description="Number of users to skip for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of users to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of all users (admin only).
    
    Args:
        skip: Number of users to skip for pagination
        limit: Maximum number of users to return (1-100)
        current_user: Current authenticated user (must be admin)
        db: Database session dependency
        
    Returns:
        List of user profile information
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 400 if pagination parameters are invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        users_list = user_controller.get_user_list(db, current_user, skip, limit)
        return users_list
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users list"
        )


# Health check endpoint for user routes
@router.get(
    "/health",
    summary="User service health check",
    description="Check if user service is operational"
)
def user_health_check():
    """
    Health check endpoint for user service.
    
    Returns:
        Service status information
    """
    return {
        "service": "user_management",
        "status": "healthy",
        "endpoints": [
            "/user/profile",
            "/user/protected",
            "/users"
        ]
    }


# Note: admin_router is exported separately and included in main.py
