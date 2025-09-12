"""
User Controller for handling user-related business logic.

This controller orchestrates user operations by coordinating
between user services, handling validation, and managing
business rules for user profiles and administration.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import user_service
from app.schemas.user import UserUpdate, UserResponse
from app.models.user import User


class UserController:
    """Controller for user-related business logic."""

    def get_current_user_profile(self, user: Optional[User]) -> UserResponse:
        """
        Get the current user's profile.
        
        Args:
            user: Current authenticated user
            
        Returns:
            User profile response
            
        Raises:
            HTTPException: If user is not authenticated
        """
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        return UserResponse.model_validate(user)

    def update_user_profile(
        self, 
        db: Session, 
        user: Optional[User], 
        update_data: UserUpdate
    ) -> UserResponse:
        """
        Update the current user's profile.
        
        Args:
            db: Database session
            user: Current authenticated user
            update_data: Profile update data
            
        Returns:
            Updated user profile response
            
        Raises:
            HTTPException: If update fails due to validation or business rules
        """
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        try:
            # Update user through service layer
            updated_user = user_service.update_user(db, user.id, update_data)
            
            return UserResponse.model_validate(updated_user)
            
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

    def get_user_list(
        self, 
        db: Session, 
        current_user: Optional[User], 
        skip: int = 0, 
        limit: int = 100
    ) -> List[UserResponse]:
        """
        Get a list of users (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated user
            skip: Number of users to skip for pagination
            limit: Maximum number of users to return
            
        Returns:
            List of user profile responses
            
        Raises:
            HTTPException: If user is not authenticated, not admin, or validation fails
        """
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Check admin privileges (for now, we'll use a simple check)
        # In a real application, this would check a role or permission system
        if not self._is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Validate pagination parameters
        if skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip cannot be negative"
            )
        
        if limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be positive"
            )
        
        if limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit cannot exceed 100"
            )
        
        try:
            # Get users through service layer
            users = user_service.get_users(db, skip=skip, limit=limit)
            
            return [UserResponse.model_validate(user) for user in users]
            
        except Exception as e:
            # Handle unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    def _is_admin_user(self, user: User) -> bool:
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
