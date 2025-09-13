"""
Dashboard Controller for handling admin dashboard and analytics operations.

This controller orchestrates dashboard operations by coordinating
between analytics services, handling validation, and managing
business rules for admin dashboard functionality.
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services.analytics_service import (
    get_dashboard_stats,
    search_users,
    bulk_activate_users,
    bulk_deactivate_users,
    export_users_csv,
    export_users_json
)
from app.schemas.analytics import (
    DashboardStats,
    UserSearchFilters,
    UserSearchResult,
    BulkUserOperation,
    BulkOperationResult,
    UserExportRequest
)
from app.models.user import User


class DashboardController:
    """Controller for dashboard-related business logic."""

    def get_dashboard_statistics(
        self, 
        db: Session, 
        current_user: Optional[User]
    ) -> DashboardStats:
        """
        Get dashboard statistics (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated user
            
        Returns:
            Dashboard statistics
            
        Raises:
            HTTPException: If user is not authenticated or not admin
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
        
        try:
            stats = get_dashboard_stats(db)
            return stats
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve dashboard statistics"
            )

    def search_users(
        self,
        db: Session,
        current_user: Optional[User],
        filters: UserSearchFilters
    ) -> UserSearchResult:
        """
        Search users with advanced filtering (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated user
            filters: Search filters and pagination parameters
            
        Returns:
            Search results with users and pagination info
            
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
        if filters.skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip cannot be negative"
            )
        
        if filters.limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be positive"
            )
        
        if filters.limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit too large (maximum 1000)"
            )
        
        try:
            result = search_users(db, filters)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search users"
            )

    def bulk_user_operation(
        self,
        db: Session,
        current_user: Optional[User],
        operation: BulkUserOperation
    ) -> BulkOperationResult:
        """
        Perform bulk operations on users (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated user
            operation: Bulk operation details
            
        Returns:
            Results of the bulk operation
            
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
        
        # Validate operation
        if not operation.user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user IDs provided"
            )
        
        if len(operation.user_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many users (maximum 100 per operation)"
            )
        
        if operation.operation not in ["activate", "deactivate"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid operation. Must be 'activate' or 'deactivate'"
            )
        
        try:
            if operation.operation == "activate":
                result = bulk_activate_users(
                    db, 
                    operation.user_ids, 
                    requesting_user_id=current_user.id
                )
            else:  # deactivate
                result = bulk_deactivate_users(
                    db, 
                    operation.user_ids, 
                    requesting_user_id=current_user.id
                )
            
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to perform bulk operation: {str(e)}"
            )

    def export_users(
        self,
        db: Session,
        current_user: Optional[User],
        export_request: UserExportRequest
    ) -> str:
        """
        Export users data (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated user
            export_request: Export configuration
            
        Returns:
            Exported data as string
            
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
        
        # Validate export format
        if export_request.format not in ["csv", "json"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported format. Must be 'csv' or 'json'"
            )
        
        try:
            # Apply filters if provided
            filters = export_request.filters
            if not export_request.include_inactive:
                # Create or modify filters to exclude inactive users
                if filters is None:
                    from app.schemas.analytics import UserSearchFilters
                    filters = UserSearchFilters(is_active=True)
                else:
                    filters.is_active = True
            
            if export_request.format == "csv":
                content = export_users_csv(db, filters)
            else:  # json
                content = export_users_json(db, filters)
            
            return content
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to export users: {str(e)}"
            )

    def _is_admin_user(self, user: User) -> bool:
        """
        Check if user has admin privileges.
        
        Args:
            user: User to check
            
        Returns:
            True if user is admin and active, False otherwise
        """
        return user.role == "admin" and user.is_active

    def get_user_analytics(
        self,
        db: Session,
        current_user: Optional[User]
    ) -> dict:
        """
        Get detailed user analytics (admin only).
        
        Args:
            db: Database session
            current_user: Current authenticated user
            
        Returns:
            Dictionary with detailed analytics
            
        Raises:
            HTTPException: If user is not authenticated or not admin
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
        
        try:
            from app.services.analytics_service import get_user_statistics
            analytics = get_user_statistics(db)
            return analytics
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user analytics"
            )

    def validate_search_parameters(self, filters: UserSearchFilters) -> None:
        """
        Validate search parameters.
        
        Args:
            filters: Search filters to validate
            
        Raises:
            HTTPException: If validation fails
        """
        if filters.skip < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Skip parameter cannot be negative"
            )
        
        if filters.limit <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit parameter must be positive"
            )
        
        if filters.limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit parameter too large (maximum 1000)"
            )
        
        # Validate sort parameters
        valid_sort_fields = ["id", "username", "role", "is_active", "created_at", "updated_at"]
        if filters.sort_by and filters.sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}"
            )
        
        valid_sort_orders = ["asc", "desc"]
        if filters.sort_order and filters.sort_order not in valid_sort_orders:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid sort order. Must be one of: {', '.join(valid_sort_orders)}"
            )
        
        # Validate date range
        if filters.created_after and filters.created_before:
            if filters.created_after > filters.created_before:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="created_after cannot be later than created_before"
                )

    def validate_bulk_operation(self, operation: BulkUserOperation) -> None:
        """
        Validate bulk operation parameters.
        
        Args:
            operation: Bulk operation to validate
            
        Raises:
            HTTPException: If validation fails
        """
        if not operation.user_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No user IDs provided"
            )
        
        if len(operation.user_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many users (maximum 100 per operation)"
            )
        
        # Check for duplicate user IDs
        if len(operation.user_ids) != len(set(operation.user_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate user IDs are not allowed"
            )
        
        # Validate user IDs are positive integers
        for user_id in operation.user_ids:
            if not isinstance(user_id, int) or user_id <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All user IDs must be positive integers"
                )
        
        valid_operations = ["activate", "deactivate"]
        if operation.operation not in valid_operations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid operation. Must be one of: {', '.join(valid_operations)}"
            )
