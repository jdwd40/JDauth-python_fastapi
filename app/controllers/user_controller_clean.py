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
from app.schemas.user import UserUpdate, UserResponse, UserCreate
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
        
        # Check admin privileges
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
        
        Args:
            user: User to check
            
        Returns:
            True if user has admin privileges and is active
        """
        # Check role field and active status
        return user.role == "admin" and user.is_active

    # Admin CRUD operations
    def admin_create_user(
        self, 
        db: Session, 
        current_user: Optional[User], 
        user_data: UserCreate
    ) -> UserResponse:
        """
        Create a new user (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated admin user
            user_data: User creation data
            
        Returns:
            Created user profile response
            
        Raises:
            HTTPException: If creation fails due to validation or business rules
        """
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Admin check is done by the require_admin dependency, but double-check
        if not self._is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        try:
            # Create user through service layer
            created_user = user_service.create_user(db, user_data)
            
            return UserResponse.model_validate(created_user)
            
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

    def admin_get_user_by_id(
        self, 
        db: Session, 
        current_user: Optional[User], 
        user_id: int
    ) -> UserResponse:
        """
        Get a specific user by ID (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated admin user
            user_id: ID of the user to retrieve
            
        Returns:
            User profile response
            
        Raises:
            HTTPException: If user not found or access denied
        """
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Admin check is done by the require_admin dependency, but double-check
        if not self._is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Validate user_id
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID must be positive"
            )
        
        try:
            # Get user through service layer
            user = user_service.get_user_by_id(db, user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return UserResponse.model_validate(user)
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    def admin_update_user(
        self, 
        db: Session, 
        current_user: Optional[User], 
        user_id: int, 
        update_data: UserUpdate
    ) -> UserResponse:
        """
        Update a user's information (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated admin user
            user_id: ID of the user to update
            update_data: User update data
            
        Returns:
            Updated user profile response
            
        Raises:
            HTTPException: If update fails due to validation, business rules, or permissions
        """
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Admin check is done by the require_admin dependency, but double-check
        if not self._is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Validate user_id
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID must be positive"
            )
        
        # Safety check: prevent admin from modifying their own account
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify your own account"
            )
        
        try:
            # Update user through service layer
            updated_user = user_service.update_user(db, user_id, update_data)
            
            return UserResponse.model_validate(updated_user)
            
        except ValueError as e:
            # Handle business rule violations (user not found, duplicate username, etc.)
            if "not found" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            else:
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

    def admin_delete_user(
        self, 
        db: Session, 
        current_user: Optional[User], 
        user_id: int
    ) -> dict:
        """
        Delete a user (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated admin user
            user_id: ID of the user to delete
            
        Returns:
            Deletion confirmation message
            
        Raises:
            HTTPException: If deletion fails due to permissions or user not found
        """
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Admin check is done by the require_admin dependency, but double-check
        if not self._is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Validate user_id
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID must be positive"
            )
        
        # Safety check: prevent admin from deleting their own account
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete your own account"
            )
        
        try:
            # Delete user through service layer
            result = user_service.delete_user(db, user_id)
            
            return {"message": "User deleted successfully"}
            
        except ValueError as e:
            # Handle business rule violations (user not found, etc.)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            # Handle unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    # Role Management Methods
    
    def assign_user_role(
        self, 
        db: Session, 
        current_user: Optional[User], 
        user_id: int, 
        role: str
    ) -> UserResponse:
        """
        Assign a role to a user (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated admin user
            user_id: ID of the user to update
            role: Role to assign
            
        Returns:
            Updated user profile response
            
        Raises:
            HTTPException: If operation fails due to permissions or business rules
        """
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Admin check is done by the require_admin dependency, but double-check
        if not self._is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Validate user_id
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID must be positive"
            )
        
        try:
            # Assign role through service layer
            updated_user = user_service.assign_user_role(
                db, 
                user_id, 
                role, 
                requesting_user_id=current_user.id
            )
            
            return UserResponse.model_validate(updated_user)
            
        except ValueError as e:
            # Handle business rule violations
            if "not found" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            elif "cannot modify your own" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            else:
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

    def set_user_status(
        self, 
        db: Session, 
        current_user: Optional[User], 
        user_id: int, 
        is_active: bool
    ) -> UserResponse:
        """
        Set a user's active status (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated admin user
            user_id: ID of the user to update
            is_active: Active status to set
            
        Returns:
            Updated user profile response
            
        Raises:
            HTTPException: If operation fails due to permissions or business rules
        """
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Admin check is done by the require_admin dependency, but double-check
        if not self._is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Validate user_id
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID must be positive"
            )
        
        try:
            # Set status through service layer
            updated_user = user_service.set_user_status(
                db, 
                user_id, 
                is_active, 
                requesting_user_id=current_user.id
            )
            
            return UserResponse.model_validate(updated_user)
            
        except ValueError as e:
            # Handle business rule violations
            if "not found" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            elif "cannot modify your own" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            else:
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
