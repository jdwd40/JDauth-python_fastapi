"""
User routes for the JDauth FastAPI application.

This module contains all user-related API endpoints including
profile management, protected routes, and user administration.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers.user_controller import UserController
from app.controllers.dashboard_controller import DashboardController
from app.schemas.user import UserResponse, UserUpdate, UserCreate, UserRoleAssignment, UserStatusUpdate
from app.schemas.analytics import (
    DashboardStats,
    UserSearchFilters,
    UserSearchResult,
    BulkUserOperation,
    BulkOperationResult,
    UserExportRequest
)
from app.schemas.audit import AuditLogSearchResult, AuditLogResponse
from app.utils.dependencies import get_current_user, require_admin
from app.models.user import User

# Create router instance
router = APIRouter(prefix="/user", tags=["User Management"])

# Initialize controllers
user_controller = UserController()
dashboard_controller = DashboardController()


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
    description="Retrieve a paginated list of all users with optional filtering. Requires admin privileges."
)
def get_users_list(
    skip: int = Query(0, ge=0, description="Number of users to skip for pagination"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of users to return"),
    role: Optional[str] = Query(None, description="Filter by user role (admin/user)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of all users (admin only).
    
    Args:
        skip: Number of users to skip for pagination
        limit: Maximum number of users to return (1-100)
        role: Optional role filter (admin/user)
        is_active: Optional active status filter
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
        users_list = user_controller.get_user_list(db, current_user, skip, limit, role, is_active)
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


# Task 3: Enhanced User Management Features

@admin_router.get(
    "/admin/dashboard/stats",
    response_model=DashboardStats,
    summary="Get dashboard statistics (Admin only)",
    description="Retrieve comprehensive dashboard statistics including user counts and growth data. Requires admin privileges."
)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics (admin only).
    
    Args:
        current_user: Current authenticated user (must be admin)
        db: Database session dependency
        
    Returns:
        Dashboard statistics including user counts and growth data
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 500 if internal server error occurs
    """
    try:
        stats = dashboard_controller.get_dashboard_statistics(db, current_user)
        return stats
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )


@admin_router.get(
    "/admin/users/search",
    response_model=UserSearchResult,
    summary="Advanced user search (Admin only)",
    description="Search users with advanced filtering, sorting, and pagination. Requires admin privileges."
)
def search_users(
    query: Optional[str] = Query(None, description="Search query for username"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    created_after: Optional[str] = Query(None, description="Filter users created after this date (ISO format)"),
    created_before: Optional[str] = Query(None, description="Filter users created before this date (ISO format)"),
    skip: int = Query(0, ge=0, description="Number of users to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    sort_by: Optional[str] = Query("created_at", description="Field to sort by"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Advanced user search with filtering and pagination (admin only).
    
    Args:
        query: Optional search query for username
        role: Optional role filter
        is_active: Optional active status filter
        created_after: Optional date filter (users created after)
        created_before: Optional date filter (users created before)
        skip: Number of users to skip for pagination
        limit: Maximum number of users to return
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        current_user: Current authenticated user (must be admin)
        db: Database session dependency
        
    Returns:
        Search results with users and pagination info
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 400 if parameters are invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        from datetime import datetime
        
        # Parse date filters if provided
        created_after_dt = None
        created_before_dt = None
        
        if created_after:
            try:
                created_after_dt = datetime.fromisoformat(created_after.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid created_after date format. Use ISO format."
                )
        
        if created_before:
            try:
                created_before_dt = datetime.fromisoformat(created_before.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid created_before date format. Use ISO format."
                )
        
        # Create filters object
        filters = UserSearchFilters(
            query=query,
            role=role,
            is_active=is_active,
            created_after=created_after_dt,
            created_before=created_before_dt,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = dashboard_controller.search_users(db, current_user, filters)
        return result
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search users"
        )


@admin_router.post(
    "/admin/users/bulk",
    response_model=BulkOperationResult,
    summary="Bulk user operations (Admin only)",
    description="Perform bulk operations on multiple users (activate/deactivate). Requires admin privileges."
)
def bulk_user_operation(
    operation: BulkUserOperation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform bulk operations on users (admin only).
    
    Args:
        operation: Bulk operation details (user IDs and operation type)
        current_user: Current authenticated user (must be admin)
        db: Database session dependency
        
    Returns:
        Results of the bulk operation
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 400 if operation parameters are invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        result = dashboard_controller.bulk_user_operation(db, current_user, operation)
        return result
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk operation"
        )


@admin_router.post(
    "/admin/users/export",
    summary="Export users data (Admin only)",
    description="Export users data in CSV or JSON format with optional filtering. Requires admin privileges."
)
def export_users(
    export_request: UserExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export users data (admin only).
    
    Args:
        export_request: Export configuration (format, filters, options)
        current_user: Current authenticated user (must be admin)
        db: Database session dependency
        
    Returns:
        Exported data as file download
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 400 if export parameters are invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        from datetime import datetime
        
        content = dashboard_controller.export_users(db, current_user, export_request)
        
        # Set appropriate content type and headers
        if export_request.format == "csv":
            media_type = "text/csv"
            filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:  # json
            media_type = "application/json"
            filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export users"
        )


# Existing Admin CRUD Routes

@admin_router.post(
    "/admin/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user (Admin only)",
    description="Create a new user account. Requires admin privileges."
)
def admin_create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only).
    
    Args:
        user_data: User creation data
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        Created user profile information
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 400 if validation fails or username exists
        HTTPException: 500 if internal server error occurs
    """
    try:
        created_user = user_controller.admin_create_user(db, current_user, user_data)
        return created_user
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@admin_router.get(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (Admin only)",
    description="Retrieve detailed information about a specific user. Requires admin privileges."
)
def admin_get_user_by_id(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID (admin only).
    
    Args:
        user_id: ID of the user to retrieve
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        User profile information
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 404 if user not found
        HTTPException: 400 if user_id is invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        user_info = user_controller.admin_get_user_by_id(db, current_user, user_id)
        return user_info
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )


@admin_router.put(
    "/admin/users/{user_id}",
    response_model=UserResponse,
    summary="Update user (Admin only)",
    description="Update user information. Requires admin privileges. Admins cannot modify their own accounts."
)
def admin_update_user(
    user_id: int,
    update_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a user's information (admin only).
    
    Args:
        user_id: ID of the user to update
        update_data: User update data
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        Updated user profile information
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin or trying to modify own account
        HTTPException: 404 if user not found
        HTTPException: 400 if validation fails or username exists
        HTTPException: 500 if internal server error occurs
    """
    try:
        updated_user = user_controller.admin_update_user(db, current_user, user_id, update_data)
        return updated_user
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@admin_router.delete(
    "/admin/users/{user_id}",
    summary="Delete user (Admin only)",
    description="Delete a user account. Requires admin privileges. Admins cannot delete their own accounts."
)
def admin_delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin only).
    
    Args:
        user_id: ID of the user to delete
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        Deletion confirmation message
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin or trying to delete own account
        HTTPException: 404 if user not found
        HTTPException: 400 if user_id is invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        result = user_controller.admin_delete_user(db, current_user, user_id)
        return result
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@admin_router.put(
    "/admin/users/{user_id}/role",
    response_model=UserResponse,
    summary="Assign role to user (Admin only)",
    description="Assign a role to a specific user. Requires admin privileges. Admins cannot modify their own roles."
)
def assign_user_role(
    user_id: int,
    role_data: UserRoleAssignment,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Assign a role to a user (admin only).
    
    Args:
        user_id: ID of the user to update
        role_data: Role assignment data
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        Updated user profile information
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin or trying to modify own role
        HTTPException: 404 if user not found
        HTTPException: 400 if validation fails or invalid role
        HTTPException: 500 if internal server error occurs
    """
    try:
        updated_user = user_controller.assign_user_role(
            db, 
            current_user, 
            user_id, 
            role_data.role.value
        )
        return updated_user
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign user role"
        )


@admin_router.put(
    "/admin/users/{user_id}/status",
    response_model=UserResponse,
    summary="Set user status (Admin only)",
    description="Set user active/inactive status. Requires admin privileges. Admins cannot modify their own status."
)
def set_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Set a user's active status (admin only).
    
    Args:
        user_id: ID of the user to update
        status_data: Status update data
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        Updated user profile information
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin or trying to modify own status
        HTTPException: 404 if user not found
        HTTPException: 400 if validation fails
        HTTPException: 500 if internal server error occurs
    """
    try:
        updated_user = user_controller.set_user_status(
            db, 
            current_user, 
            user_id, 
            status_data.is_active
        )
        return updated_user
    except HTTPException:
        # Re-raise HTTP exceptions from controller
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set user status"
        )


# Task 4: Security & Audit System - Audit Log Endpoints

@admin_router.get(
    "/admin/audit/logs",
    response_model=AuditLogSearchResult,
    summary="Get audit logs (Admin only)",
    description="Retrieve audit logs with filtering and pagination. Requires admin privileges."
)
def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by audit action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    username: Optional[str] = Query(None, description="Filter by username"),
    status: Optional[str] = Query(None, description="Filter by status (success/failed/error)"),
    is_security_event: Optional[str] = Query(None, description="Filter by security event type"),
    severity_level: Optional[str] = Query(None, description="Filter by severity level"),
    created_after: Optional[str] = Query(None, description="Filter logs created after this date (ISO format)"),
    created_before: Optional[str] = Query(None, description="Filter logs created before this date (ISO format)"),
    skip: int = Query(0, ge=0, description="Number of logs to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit logs with filtering and pagination (admin only).
    
    Args:
        action: Optional audit action filter
        resource_type: Optional resource type filter
        user_id: Optional user ID filter
        username: Optional username filter
        status: Optional status filter
        is_security_event: Optional security event filter
        severity_level: Optional severity level filter
        created_after: Optional date filter (logs created after)
        created_before: Optional date filter (logs created before)
        skip: Number of logs to skip for pagination
        limit: Maximum number of logs to return
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        Audit logs with pagination information
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 400 if parameters are invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        from datetime import datetime
        from app.schemas.audit import AuditLogFilters, AuditAction, AuditStatus, SecurityEventType, SeverityLevel
        from app.services.audit_service import get_audit_logs
        
        # Parse date filters if provided
        created_after_dt = None
        created_before_dt = None
        
        if created_after:
            try:
                created_after_dt = datetime.fromisoformat(created_after.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid created_after date format. Use ISO format."
                )
        
        if created_before:
            try:
                created_before_dt = datetime.fromisoformat(created_before.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid created_before date format. Use ISO format."
                )
        
        # Convert string filters to enums
        action_enum = None
        if action:
            try:
                action_enum = AuditAction(action)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid action: {action}"
                )
        
        status_enum = None
        if status:
            try:
                status_enum = AuditStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}"
                )
        
        security_event_enum = None
        if is_security_event:
            try:
                security_event_enum = SecurityEventType(is_security_event)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid security event type: {is_security_event}"
                )
        
        severity_enum = None
        if severity_level:
            try:
                severity_enum = SeverityLevel(severity_level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity level: {severity_level}"
                )
        
        # Create filters object
        filters = AuditLogFilters(
            action=action_enum,
            resource_type=resource_type,
            user_id=user_id,
            username=username,
            status=status_enum,
            is_security_event=security_event_enum,
            severity_level=severity_enum,
            created_after=created_after_dt,
            created_before=created_before_dt,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = get_audit_logs(db, filters)
        
        # Log the audit log access
        from app.services.audit_service import log_user_action
        log_user_action(
            db=db,
            action=AuditAction.VIEW_AUDIT_LOGS,
            user_id=current_user.id,
            username=current_user.username,
            description=f"Viewed audit logs with filters: {filters.dict()}",
            details={"filters": filters.dict()}
        )
        
        return result
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@admin_router.get(
    "/admin/audit/security-events",
    response_model=List[AuditLogResponse],
    summary="Get security events (Admin only)",
    description="Retrieve recent security events. Requires admin privileges."
)
def get_security_events(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of events to return"),
    severity_level: Optional[str] = Query(None, description="Filter by severity level"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get recent security events (admin only).
    
    Args:
        limit: Maximum number of events to return
        severity_level: Optional severity level filter
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        List of security event audit logs
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 400 if parameters are invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        from app.schemas.audit import SeverityLevel
        from app.services.audit_service import get_security_events
        
        # Convert string filter to enum
        severity_enum = None
        if severity_level:
            try:
                severity_enum = SeverityLevel(severity_level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity level: {severity_level}"
                )
        
        events = get_security_events(db, limit=limit, severity_level=severity_enum)
        
        # Log the security events access
        from app.services.audit_service import log_user_action
        log_user_action(
            db=db,
            action=AuditAction.VIEW_AUDIT_LOGS,
            user_id=current_user.id,
            username=current_user.username,
            description=f"Viewed security events (limit: {limit}, severity: {severity_level})",
            details={"limit": limit, "severity_level": severity_level}
        )
        
        return events
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security events"
        )


@admin_router.get(
    "/admin/security/summary",
    summary="Get security summary (Admin only)",
    description="Get a summary of recent security events and statistics. Requires admin privileges."
)
def get_security_summary(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to look back"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get security summary (admin only).
    
    Args:
        hours: Number of hours to look back
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        Security summary with event statistics
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 400 if parameters are invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        from app.services.security_service import SecurityService
        
        summary = SecurityService.get_security_summary(db, hours=hours)
        
        # Log the security summary access
        from app.services.audit_service import log_user_action
        log_user_action(
            db=db,
            action=AuditAction.ACCESS_ADMIN_DASHBOARD,
            user_id=current_user.id,
            username=current_user.username,
            description=f"Accessed security summary (hours: {hours})",
            details={"hours": hours, "summary": summary}
        )
        
        return summary
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security summary"
        )


@admin_router.get(
    "/admin/audit/users/{user_id}/logs",
    response_model=List[AuditLogResponse],
    summary="Get user audit logs (Admin only)",
    description="Get audit logs for a specific user. Requires admin privileges."
)
def get_user_audit_logs(
    user_id: int,
    limit: int = Query(50, ge=1, le=200, description="Maximum number of logs to return"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit logs for a specific user (admin only).
    
    Args:
        user_id: ID of the user to get logs for
        limit: Maximum number of logs to return
        current_user: Current authenticated admin user
        db: Database session dependency
        
    Returns:
        List of audit logs for the user
        
    Raises:
        HTTPException: 401 if user is not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 404 if user not found
        HTTPException: 400 if parameters are invalid
        HTTPException: 500 if internal server error occurs
    """
    try:
        from app.services.audit_service import get_user_audit_logs
        from app.services.user_service import get_user_by_id
        
        # Verify user exists
        target_user = get_user_by_id(db, user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logs = get_user_audit_logs(db, user_id=user_id, limit=limit)
        
        # Log the user audit logs access
        from app.services.audit_service import log_user_action
        log_user_action(
            db=db,
            action=AuditAction.VIEW_AUDIT_LOGS,
            user_id=current_user.id,
            username=current_user.username,
            target_user_id=user_id,
            target_username=target_user.username,
            description=f"Viewed audit logs for user '{target_user.username}'",
            details={"target_user_id": user_id, "limit": limit}
        )
        
        return logs
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user audit logs"
        )


# Note: admin_router is exported separately and included in main.py
