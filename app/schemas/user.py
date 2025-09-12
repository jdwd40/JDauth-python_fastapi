"""
User-related Pydantic schemas for input validation and output serialization.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserCreate(BaseModel):
    """Schema for user registration input validation."""
    username: str = Field(..., min_length=3, max_length=50, description="Username must be 3-50 characters")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "secure_password123"
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for user profile update input validation."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="New username (optional)")
    password: Optional[str] = Field(None, min_length=6, description="New password (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "new_username",
                "password": "new_secure_password123"
            }
        }
    )


class UserResponse(BaseModel):
    """Schema for user data output serialization (public data only)."""
    id: int
    username: str
    created_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "johndoe",
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
