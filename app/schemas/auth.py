"""
Authentication-related Pydantic schemas for input validation and output serialization.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from .user import UserResponse


class LoginRequest(BaseModel):
    """Schema for user login credentials validation."""
    username: str = Field(..., min_length=1, description="Username for login")
    password: str = Field(..., min_length=1, description="Password for login")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "password": "secure_password123"
            }
        }
    )


class TokenResponse(BaseModel):
    """Schema for JWT token response format."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration time in seconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }
    )


class TokenData(BaseModel):
    """Schema for JWT token payload structure."""
    username: Optional[str] = None
    expires_at: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "johndoe",
                "expires_at": "2023-12-01T12:30:00Z"
            }
        }
    )


class UserAuth(BaseModel):
    """Schema for user authentication response including user data and token."""
    user: UserResponse
    token: TokenResponse

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "id": 1,
                    "username": "johndoe",
                    "created_at": "2023-12-01T10:30:00Z"
                },
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800
                }
            }
        }
    )
