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

from .audit_service import (
    log_audit_event,
    log_user_action,
    log_authentication_event,
    log_security_event,
    get_audit_logs,
    get_security_events,
    get_user_audit_logs,
    get_recent_audit_logs
)

from .security_service import (
    SecurityService,
    admin_rate_limiter,
    auth_rate_limiter,
    failed_login_tracker
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
    "get_user_statistics",
    
    # Audit service
    "log_audit_event",
    "log_user_action",
    "log_authentication_event",
    "log_security_event",
    "get_audit_logs",
    "get_security_events",
    "get_user_audit_logs",
    "get_recent_audit_logs",
    
    # Security service
    "SecurityService",
    "admin_rate_limiter",
    "auth_rate_limiter",
    "failed_login_tracker"
]
