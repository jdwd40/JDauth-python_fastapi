"""
Audit-related Pydantic schemas for input validation and output serialization.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class AuditAction(str, Enum):
    """Enumeration of audit actions."""
    # User management actions
    CREATE_USER = "CREATE_USER"
    UPDATE_USER = "UPDATE_USER"
    DELETE_USER = "DELETE_USER"
    CHANGE_USER_ROLE = "CHANGE_USER_ROLE"
    SET_USER_STATUS = "SET_USER_STATUS"
    
    # Bulk operations
    BULK_ACTIVATE_USERS = "BULK_ACTIVATE_USERS"
    BULK_DEACTIVATE_USERS = "BULK_DEACTIVATE_USERS"
    
    # Authentication actions
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    
    # Security events
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    ACCOUNT_LOCKOUT = "ACCOUNT_LOCKOUT"
    
    # Admin actions
    VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"
    EXPORT_DATA = "EXPORT_DATA"
    ACCESS_ADMIN_DASHBOARD = "ACCESS_ADMIN_DASHBOARD"


class AuditStatus(str, Enum):
    """Enumeration of audit log statuses."""
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


class SeverityLevel(str, Enum):
    """Enumeration of severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SecurityEventType(str, Enum):
    """Enumeration of security event types."""
    SUSPICIOUS = "suspicious"
    CRITICAL = "critical"


class AuditLogResponse(BaseModel):
    """Schema for audit log output serialization."""
    id: int
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    description: str
    details: Optional[Dict[str, Any]] = None
    status: AuditStatus
    error_message: Optional[str] = None
    created_at: datetime
    is_security_event: Optional[SecurityEventType] = None
    severity_level: SeverityLevel

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "action": "CREATE_USER",
                "resource_type": "user",
                "resource_id": "123",
                "user_id": 1,
                "username": "admin",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "request_method": "POST",
                "request_path": "/api/admin/users",
                "description": "Created new user 'johndoe'",
                "details": {"username": "johndoe", "role": "user"},
                "status": "success",
                "error_message": None,
                "created_at": "2023-12-01T10:30:00Z",
                "is_security_event": None,
                "severity_level": "info"
            }
        }
    )


class AuditLogFilters(BaseModel):
    """Schema for filtering audit logs."""
    action: Optional[AuditAction] = None
    resource_type: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    status: Optional[AuditStatus] = None
    is_security_event: Optional[SecurityEventType] = None
    severity_level: Optional[SeverityLevel] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of records to return")
    sort_by: str = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")


class AuditLogSearchResult(BaseModel):
    """Schema for audit log search results."""
    logs: List[AuditLogResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "logs": [
                    {
                        "id": 1,
                        "action": "CREATE_USER",
                        "resource_type": "user",
                        "user_id": 1,
                        "username": "admin",
                        "description": "Created new user 'johndoe'",
                        "status": "success",
                        "created_at": "2023-12-01T10:30:00Z"
                    }
                ],
                "total_count": 150,
                "page": 1,
                "page_size": 100,
                "has_next": True,
                "has_previous": False
            }
        }
    )


class SecurityEventResponse(BaseModel):
    """Schema for security event output serialization."""
    id: int
    event_type: str
    description: str
    severity: SeverityLevel
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "event_type": "suspicious_login",
                "description": "Multiple failed login attempts detected",
                "severity": "warning",
                "user_id": 123,
                "username": "johndoe",
                "ip_address": "192.168.1.100",
                "details": {"attempt_count": 5, "time_window": "5 minutes"},
                "resolved": False,
                "resolved_at": None,
                "resolved_by": None,
                "created_at": "2023-12-01T10:30:00Z"
            }
        }
    )


class FailedLoginAttempt(BaseModel):
    """Schema for tracking failed login attempts."""
    username: str
    ip_address: str
    user_agent: Optional[str] = None
    attempted_at: datetime
    failure_reason: str  # "invalid_password", "user_not_found", "account_locked", etc.

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "attempted_at": "2023-12-01T10:30:00Z",
                "failure_reason": "invalid_password"
            }
        }
    )


class RateLimitInfo(BaseModel):
    """Schema for rate limiting information."""
    endpoint: str
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None  # Seconds to wait before retry

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "endpoint": "/api/admin/users",
                "limit": 30,
                "remaining": 25,
                "reset_time": "2023-12-01T11:00:00Z",
                "retry_after": None
            }
        }
    )
