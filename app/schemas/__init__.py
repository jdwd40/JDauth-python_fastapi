"""
Pydantic schemas for input validation and output serialization.

This module provides clean separation between:
- Input validation (UserCreate, LoginRequest, etc.)
- Output serialization (UserResponse, TokenResponse, etc.)
- Internal data handling (UserInDB, TokenData, etc.)
"""

from .user import UserCreate, UserResponse, UserUpdate, UserInDB, UserRoleAssignment, UserStatusUpdate
from .auth import LoginRequest, TokenResponse, TokenData, UserAuth
from .audit import (
    AuditAction, AuditStatus, SeverityLevel, SecurityEventType,
    AuditLogResponse, AuditLogFilters, AuditLogSearchResult,
    SecurityEventResponse, FailedLoginAttempt, RateLimitInfo
)

__all__ = [
    "UserCreate",
    "UserResponse", 
    "UserUpdate",
    "UserInDB",
    "UserRoleAssignment",
    "UserStatusUpdate",
    "LoginRequest",
    "TokenResponse",
    "TokenData",
    "UserAuth",
    "AuditAction",
    "AuditStatus",
    "SeverityLevel",
    "SecurityEventType",
    "AuditLogResponse",
    "AuditLogFilters",
    "AuditLogSearchResult",
    "SecurityEventResponse",
    "FailedLoginAttempt",
    "RateLimitInfo",
]
