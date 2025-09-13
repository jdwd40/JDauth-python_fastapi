"""
Analytics and dashboard-related Pydantic schemas for admin statistics.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class RecentRegistrations(BaseModel):
    """Schema for recent registration statistics."""
    today: int = Field(..., description="Number of registrations today")
    this_week: int = Field(..., description="Number of registrations this week")
    this_month: int = Field(..., description="Number of registrations this month")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "today": 5,
                "this_week": 23,
                "this_month": 67
            }
        }
    )


class UserGrowthPoint(BaseModel):
    """Schema for a single point in user growth data."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    total_users: int = Field(..., description="Total users on this date")
    new_users: int = Field(..., description="New users registered on this date")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2023-12-01",
                "total_users": 150,
                "new_users": 5
            }
        }
    )


class DashboardStats(BaseModel):
    """Schema for admin dashboard statistics."""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")
    admin_users: int = Field(..., description="Number of admin users")
    recent_registrations: RecentRegistrations = Field(..., description="Recent registration statistics")
    user_growth: List[UserGrowthPoint] = Field(..., description="User growth data for the last 30 days")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_users": 150,
                "active_users": 142,
                "inactive_users": 8,
                "admin_users": 3,
                "recent_registrations": {
                    "today": 5,
                    "this_week": 23,
                    "this_month": 67
                },
                "user_growth": [
                    {"date": "2023-12-01", "total_users": 150, "new_users": 5},
                    {"date": "2023-11-30", "total_users": 145, "new_users": 3}
                ]
            }
        }
    )


class UserSearchFilters(BaseModel):
    """Schema for user search filters."""
    query: Optional[str] = Field(None, description="Search query for username")
    role: Optional[str] = Field(None, description="Filter by user role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    created_after: Optional[datetime] = Field(None, description="Filter users created after this date")
    created_before: Optional[datetime] = Field(None, description="Filter users created before this date")
    skip: int = Field(0, ge=0, description="Number of users to skip for pagination")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of users to return")
    sort_by: Optional[str] = Field("created_at", description="Field to sort by")
    sort_order: Optional[str] = Field("desc", description="Sort order: asc or desc")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "john",
                "role": "user",
                "is_active": True,
                "created_after": "2023-11-01T00:00:00Z",
                "created_before": "2023-12-01T00:00:00Z",
                "skip": 0,
                "limit": 50,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }
    )


class UserSearchResult(BaseModel):
    """Schema for user search results."""
    users: List[Dict[str, Any]] = Field(..., description="List of users matching the search criteria")
    total_count: int = Field(..., description="Total number of users matching the criteria")
    page_info: Dict[str, Any] = Field(..., description="Pagination information")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "users": [
                    {
                        "id": 1,
                        "username": "johndoe",
                        "role": "user",
                        "is_active": True,
                        "created_at": "2023-12-01T10:30:00Z"
                    }
                ],
                "total_count": 1,
                "page_info": {
                    "current_page": 1,
                    "total_pages": 1,
                    "has_next": False,
                    "has_previous": False
                }
            }
        }
    )


class BulkUserOperation(BaseModel):
    """Schema for bulk user operations."""
    user_ids: List[int] = Field(..., description="List of user IDs to operate on")
    operation: str = Field(..., description="Operation to perform: activate, deactivate")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_ids": [1, 2, 3],
                "operation": "activate"
            }
        }
    )


class BulkOperationResult(BaseModel):
    """Schema for bulk operation results."""
    successful: List[int] = Field(..., description="User IDs that were successfully processed")
    failed: List[Dict[str, Any]] = Field(..., description="User IDs that failed with error messages")
    total_processed: int = Field(..., description="Total number of users processed")
    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "successful": [1, 2],
                "failed": [
                    {"user_id": 3, "error": "User not found"}
                ],
                "total_processed": 3,
                "success_count": 2,
                "failure_count": 1
            }
        }
    )


class UserExportRequest(BaseModel):
    """Schema for user export requests."""
    format: str = Field("csv", description="Export format: csv, json")
    filters: Optional[UserSearchFilters] = Field(None, description="Optional filters to apply")
    include_inactive: bool = Field(True, description="Whether to include inactive users")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "format": "csv",
                "filters": {
                    "role": "user",
                    "is_active": True
                },
                "include_inactive": False
            }
        }
    )
