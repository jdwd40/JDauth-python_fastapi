"""
User-related Pydantic schemas for input validation and output serialization.
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class UserRole(str, Enum):
    """Enumeration of user roles."""
    ADMIN = "admin"
    USER = "user"


class UserCreate(BaseModel):
    """Schema for user registration input validation."""
    username: str = Field(..., min_length=3, max_length=50, description="Username must be 3-50 characters")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    role: Optional[UserRole] = Field(default=UserRole.USER, description="User role (defaults to 'user')")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "secure_password123",
                "role": "user"
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for user profile update input validation."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username (optional)")
    password: Optional[str] = Field(None, min_length=6, description="New password (optional)")
    role: Optional[UserRole] = Field(None, description="New user role (optional)")
    is_active: Optional[bool] = Field(None, description="User active status (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "new_username",
                "password": "new_secure_password123",
                "role": "user",
                "is_active": True
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user data output serialization (public data only)."""
    id: int
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "johndoe",
                "role": "user",
                "is_active": True,
                "created_at": "2023-12-01T10:30:00Z"
            }
        }
    )


class UserInDB(UserResponse):
    """Schema for internal user representation including sensitive data."""
    hashed_password: str
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class UserRoleAssignment(BaseModel):
    """Schema for role assignment requests."""
    role: UserRole = Field(..., description="Role to assign to the user")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "admin"
            }
        }
    )


class UserStatusUpdate(BaseModel):
    """Schema for user status update requests."""
    is_active: bool = Field(..., description="Active status to set for the user")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_active": False
            }
        }
    )
