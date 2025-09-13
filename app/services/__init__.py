"""
Service layer for business logic and data access operations.
"""

from .user_service import (
    create_user,
    get_user_by_username,
    get_user_by_id,
    update_user,
    delete_user,
    get_users
)

from .auth_service import (
    authenticate_user,
    create_access_token,
    verify_token,
    get_current_user_from_token
)

from .analytics_service import (
    get_dashboard_stats,
    search_users,
    bulk_activate_users,
    bulk_deactivate_users,
    export_users_csv,
    export_users_json,
    get_user_growth_data,
    count_recent_registrations,
    get_user_statistics
)

__all__ = [
    # User service
    "create_user",
    "get_user_by_username", 
    "get_user_by_id",
    "update_user",
    "delete_user",
    "get_users",
    
    # Auth service
    "authenticate_user",
    "create_access_token",
    "verify_token",
    "get_current_user_from_token",
    
    # Analytics service
    "get_dashboard_stats",
    "search_users",
    "bulk_activate_users",
    "bulk_deactivate_users",
    "export_users_csv",
    "export_users_json",
    "get_user_growth_data",
    "count_recent_registrations",
    "get_user_statistics"
]
