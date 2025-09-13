"""
Analytics service for handling dashboard statistics and user management analytics.
"""

import csv
import json
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from io import StringIO

from app.models.user import User
from app.schemas.analytics import (
    DashboardStats,
    RecentRegistrations,
    UserGrowthPoint,
    UserSearchFilters,
    UserSearchResult,
    BulkOperationResult
)
from app.schemas.user import UserResponse


def get_dashboard_stats(db: Session) -> DashboardStats:
    """
    Get comprehensive dashboard statistics.
    
    Args:
        db: Database session
        
    Returns:
        Dashboard statistics including user counts and growth data
    """
    # Get basic user counts
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    inactive_users = db.query(User).filter(User.is_active == False).count()
    admin_users = db.query(User).filter(User.role == "admin").count()
    
    # Get recent registrations
    recent_registrations = count_recent_registrations(db)
    
    # Get user growth data for the last 30 days
    user_growth = get_user_growth_data(db, days=30)
    
    return DashboardStats(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        admin_users=admin_users,
        recent_registrations=RecentRegistrations(**recent_registrations),
        user_growth=user_growth
    )


def count_recent_registrations(db: Session) -> Dict[str, int]:
    """
    Count recent user registrations.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with counts for today, this week, and this month
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)
    
    today_count = db.query(User).filter(
        User.created_at >= today_start
    ).count()
    
    week_count = db.query(User).filter(
        User.created_at >= week_start
    ).count()
    
    month_count = db.query(User).filter(
        User.created_at >= month_start
    ).count()
    
    return {
        "today": today_count,
        "this_week": week_count,
        "this_month": month_count
    }


def get_user_growth_data(db: Session, days: int = 30) -> List[Dict[str, Any]]:
    """
    Get user growth data for the specified number of days.
    
    Args:
        db: Database session
        days: Number of days to include in growth data
        
    Returns:
        List of user growth data points
    """
    if days <= 0:
        return []
    
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # Get daily registration counts
    daily_registrations = db.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('new_users')
    ).filter(
        User.created_at >= start_date
    ).group_by(
        func.date(User.created_at)
    ).order_by('date').all()
    
    # Build growth data with cumulative totals
    growth_data = []
    total_users_before = db.query(User).filter(User.created_at < start_date).count()
    running_total = total_users_before
    
    # Create a dict for easy lookup
    registration_dict = {str(reg.date): reg.new_users for reg in daily_registrations}
    
    # Generate data for each day in the range
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        new_users = registration_dict.get(date_str, 0)
        running_total += new_users
        
        growth_data.append({
            "date": date_str,
            "total_users": running_total,
            "new_users": new_users
        })
    
    return growth_data


def search_users(db: Session, filters: UserSearchFilters) -> UserSearchResult:
    """
    Search users with advanced filtering and pagination.
    
    Args:
        db: Database session
        filters: Search filters and pagination parameters
        
    Returns:
        Search results with users and pagination info
    """
    # Build the base query
    query = db.query(User)
    
    # Apply filters
    if filters.query:
        query = query.filter(User.username.ilike(f"%{filters.query}%"))
    
    if filters.role:
        query = query.filter(User.role == filters.role)
    
    if filters.is_active is not None:
        query = query.filter(User.is_active == filters.is_active)
    
    if filters.created_after:
        query = query.filter(User.created_at >= filters.created_after)
    
    if filters.created_before:
        query = query.filter(User.created_at <= filters.created_before)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply sorting
    sort_field = getattr(User, filters.sort_by, User.created_at)
    if filters.sort_order == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # Apply pagination
    users = query.offset(filters.skip).limit(filters.limit).all()
    
    # Convert users to dict format
    users_data = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        }
        users_data.append(user_dict)
    
    # Calculate pagination info
    current_page = (filters.skip // filters.limit) + 1
    total_pages = (total_count + filters.limit - 1) // filters.limit
    has_next = current_page < total_pages
    has_previous = current_page > 1
    
    page_info = {
        "current_page": current_page,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_previous": has_previous
    }
    
    return UserSearchResult(
        users=users_data,
        total_count=total_count,
        page_info=page_info
    )


def bulk_activate_users(
    db: Session, 
    user_ids: List[int], 
    requesting_user_id: Optional[int] = None
) -> BulkOperationResult:
    """
    Bulk activate users.
    
    Args:
        db: Database session
        user_ids: List of user IDs to activate
        requesting_user_id: ID of user making the request (for safety checks)
        
    Returns:
        Results of the bulk operation
    """
    successful = []
    failed = []
    
    for user_id in user_ids:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                failed.append({"user_id": user_id, "error": "User not found"})
                continue
            
            user.is_active = True
            user.updated_at = datetime.now(timezone.utc)
            successful.append(user_id)
            
        except Exception as e:
            failed.append({"user_id": user_id, "error": str(e)})
    
    # Commit all changes
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        # Move all successful to failed
        for user_id in successful:
            failed.append({"user_id": user_id, "error": "Database commit failed"})
        successful = []
    
    return BulkOperationResult(
        successful=successful,
        failed=failed,
        total_processed=len(user_ids),
        success_count=len(successful),
        failure_count=len(failed)
    )


def bulk_deactivate_users(
    db: Session, 
    user_ids: List[int], 
    requesting_user_id: Optional[int] = None
) -> BulkOperationResult:
    """
    Bulk deactivate users.
    
    Args:
        db: Database session
        user_ids: List of user IDs to deactivate
        requesting_user_id: ID of user making the request (for safety checks)
        
    Returns:
        Results of the bulk operation
    """
    successful = []
    failed = []
    
    for user_id in user_ids:
        try:
            # Safety check: prevent admin from deactivating themselves
            if requesting_user_id and requesting_user_id == user_id:
                failed.append({
                    "user_id": user_id, 
                    "error": "Cannot modify your own status"
                })
                continue
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                failed.append({"user_id": user_id, "error": "User not found"})
                continue
            
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)
            successful.append(user_id)
            
        except Exception as e:
            failed.append({"user_id": user_id, "error": str(e)})
    
    # Commit all changes
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        # Move all successful to failed
        for user_id in successful:
            failed.append({"user_id": user_id, "error": "Database commit failed"})
        successful = []
    
    return BulkOperationResult(
        successful=successful,
        failed=failed,
        total_processed=len(user_ids),
        success_count=len(successful),
        failure_count=len(failed)
    )


def export_users_csv(
    db: Session, 
    filters: Optional[UserSearchFilters] = None
) -> str:
    """
    Export users to CSV format.
    
    Args:
        db: Database session
        filters: Optional filters to apply
        
    Returns:
        CSV content as string
    """
    # Get users based on filters
    if filters:
        # Use search function to apply filters
        search_result = search_users(db, filters)
        users_data = search_result.users
    else:
        # Get all users
        users = db.query(User).all()
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            })
    
    # Create CSV content
    output = StringIO()
    fieldnames = ["id", "username", "role", "is_active", "created_at"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for user_data in users_data:
        writer.writerow(user_data)
    
    return output.getvalue()


def export_users_json(
    db: Session, 
    filters: Optional[UserSearchFilters] = None
) -> str:
    """
    Export users to JSON format.
    
    Args:
        db: Database session
        filters: Optional filters to apply
        
    Returns:
        JSON content as string
    """
    # Get users based on filters
    if filters:
        # Use search function to apply filters
        search_result = search_users(db, filters)
        users_data = search_result.users
    else:
        # Get all users
        users = db.query(User).all()
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            })
    
    return json.dumps(users_data, indent=2)


def get_user_statistics(db: Session) -> Dict[str, Any]:
    """
    Get detailed user statistics for analytics.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with various user statistics
    """
    stats = {}
    
    # Basic counts
    stats["total_users"] = db.query(User).count()
    stats["active_users"] = db.query(User).filter(User.is_active == True).count()
    stats["inactive_users"] = db.query(User).filter(User.is_active == False).count()
    
    # Role distribution
    stats["admin_users"] = db.query(User).filter(User.role == "admin").count()
    stats["regular_users"] = db.query(User).filter(User.role == "user").count()
    
    # Registration trends
    now = datetime.now(timezone.utc)
    
    # Users registered in different time periods
    stats["registered_today"] = db.query(User).filter(
        User.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    stats["registered_this_week"] = db.query(User).filter(
        User.created_at >= now - timedelta(days=7)
    ).count()
    
    stats["registered_this_month"] = db.query(User).filter(
        User.created_at >= now - timedelta(days=30)
    ).count()
    
    return stats
