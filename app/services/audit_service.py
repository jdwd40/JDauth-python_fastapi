"""
Audit service for logging administrative actions and security events.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_

from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import (
    AuditAction, AuditStatus, SeverityLevel, SecurityEventType,
    AuditLogFilters, AuditLogSearchResult
)


def log_audit_event(
    db: Session,
    action: AuditAction,
    resource_type: str,
    description: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_method: Optional[str] = None,
    request_path: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status: AuditStatus = AuditStatus.SUCCESS,
    error_message: Optional[str] = None,
    is_security_event: Optional[SecurityEventType] = None,
    severity_level: SeverityLevel = SeverityLevel.INFO
) -> AuditLog:
    """
    Log an audit event to the database.
    
    Args:
        db: Database session
        action: The action that was performed
        resource_type: Type of resource affected (e.g., "user", "role")
        description: Human-readable description of the action
        user_id: ID of user performing the action
        username: Username of user performing the action
        resource_id: ID of the affected resource
        ip_address: IP address of the request
        user_agent: User agent string
        request_method: HTTP method used
        request_path: API endpoint path
        details: Additional structured data
        status: Status of the action (success/failed/error)
        error_message: Error message if action failed
        is_security_event: Whether this is a security event
        severity_level: Severity level of the event
        
    Returns:
        Created AuditLog instance
    """
    audit_log = AuditLog(
        action=action.value,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
        description=description,
        details=details,
        status=status.value,
        error_message=error_message,
        is_security_event=is_security_event.value if is_security_event else None,
        severity_level=severity_level.value,
        created_at=datetime.now(timezone.utc)
    )
    
    try:
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log
    except Exception as e:
        db.rollback()
        # Log the audit logging failure to application logs
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to log audit event: {e}")
        raise


def log_user_action(
    db: Session,
    action: AuditAction,
    user_id: int,
    username: str,
    target_user_id: Optional[int] = None,
    target_username: Optional[str] = None,
    description: str = "",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_method: Optional[str] = None,
    request_path: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status: AuditStatus = AuditStatus.SUCCESS,
    error_message: Optional[str] = None
) -> AuditLog:
    """
    Log a user-related action (create, update, delete user, etc.).
    
    Args:
        db: Database session
        action: The action performed
        user_id: ID of admin user performing the action
        username: Username of admin user performing the action
        target_user_id: ID of user being affected
        target_username: Username of user being affected
        description: Action description
        ip_address: IP address of the request
        user_agent: User agent string
        request_method: HTTP method used
        request_path: API endpoint path
        details: Additional structured data
        status: Status of the action
        error_message: Error message if action failed
        
    Returns:
        Created AuditLog instance
    """
    # Auto-generate description if not provided
    if not description:
        if action == AuditAction.CREATE_USER:
            description = f"Created new user '{target_username}'" if target_username else f"Created new user (ID: {target_user_id})"
        elif action == AuditAction.UPDATE_USER:
            description = f"Updated user '{target_username}'" if target_username else f"Updated user (ID: {target_user_id})"
        elif action == AuditAction.DELETE_USER:
            description = f"Deleted user '{target_username}'" if target_username else f"Deleted user (ID: {target_user_id})"
        elif action == AuditAction.CHANGE_USER_ROLE:
            description = f"Changed role for user '{target_username}'" if target_username else f"Changed role for user (ID: {target_user_id})"
        elif action == AuditAction.SET_USER_STATUS:
            description = f"Changed status for user '{target_username}'" if target_username else f"Changed status for user (ID: {target_user_id})"
    
    return log_audit_event(
        db=db,
        action=action,
        resource_type="user",
        resource_id=str(target_user_id) if target_user_id else None,
        user_id=user_id,
        username=username,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
        details=details,
        status=status,
        error_message=error_message
    )


def log_authentication_event(
    db: Session,
    action: AuditAction,
    username: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status: AuditStatus = AuditStatus.SUCCESS,
    error_message: Optional[str] = None,
    is_security_event: Optional[SecurityEventType] = None
) -> AuditLog:
    """
    Log an authentication-related event (login, logout, failed login).
    
    Args:
        db: Database session
        action: The authentication action
        username: Username attempting authentication
        user_id: ID of user (if authentication successful)
        ip_address: IP address of the request
        user_agent: User agent string
        details: Additional structured data
        status: Status of the action
        error_message: Error message if action failed
        is_security_event: Whether this is a security event
        
    Returns:
        Created AuditLog instance
    """
    # Auto-generate description
    if action == AuditAction.LOGIN_SUCCESS:
        description = f"Successful login for user '{username}'"
    elif action == AuditAction.LOGIN_FAILED:
        description = f"Failed login attempt for user '{username}'"
    elif action == AuditAction.LOGOUT:
        description = f"User '{username}' logged out"
    else:
        description = f"Authentication event for user '{username}'"
    
    return log_audit_event(
        db=db,
        action=action,
        resource_type="authentication",
        resource_id=str(user_id) if user_id else username,
        user_id=user_id,
        username=username,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method="POST",
        request_path="/api/auth/login",
        details=details,
        status=status,
        error_message=error_message,
        is_security_event=is_security_event
    )


def log_security_event(
    db: Session,
    action: AuditAction,
    description: str,
    severity_level: SeverityLevel = SeverityLevel.WARNING,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_method: Optional[str] = None,
    request_path: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    is_security_event: SecurityEventType = SecurityEventType.SUSPICIOUS
) -> AuditLog:
    """
    Log a security-related event.
    
    Args:
        db: Database session
        action: The security action
        description: Description of the security event
        severity_level: Severity level of the event
        user_id: ID of user involved (if applicable)
        username: Username of user involved (if applicable)
        ip_address: IP address of the request
        user_agent: User agent string
        request_method: HTTP method used
        request_path: API endpoint path
        details: Additional structured data
        is_security_event: Type of security event
        
    Returns:
        Created AuditLog instance
    """
    return log_audit_event(
        db=db,
        action=action,
        resource_type="security",
        resource_id=str(user_id) if user_id else username,
        user_id=user_id,
        username=username,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
        details=details,
        status=AuditStatus.SUCCESS,  # Security events are logged as successful detections
        is_security_event=is_security_event,
        severity_level=severity_level
    )


def get_audit_logs(
    db: Session,
    filters: AuditLogFilters
) -> AuditLogSearchResult:
    """
    Retrieve audit logs with filtering and pagination.
    
    Args:
        db: Database session
        filters: Filtering and pagination parameters
        
    Returns:
        AuditLogSearchResult with logs and pagination info
    """
    # Build query
    query = db.query(AuditLog)
    
    # Apply filters
    if filters.action:
        query = query.filter(AuditLog.action == filters.action.value)
    
    if filters.resource_type:
        query = query.filter(AuditLog.resource_type == filters.resource_type)
    
    if filters.user_id:
        query = query.filter(AuditLog.user_id == filters.user_id)
    
    if filters.username:
        query = query.filter(AuditLog.username.ilike(f"%{filters.username}%"))
    
    if filters.status:
        query = query.filter(AuditLog.status == filters.status.value)
    
    if filters.is_security_event:
        query = query.filter(AuditLog.is_security_event == filters.is_security_event.value)
    
    if filters.severity_level:
        query = query.filter(AuditLog.severity_level == filters.severity_level.value)
    
    if filters.created_after:
        query = query.filter(AuditLog.created_at >= filters.created_after)
    
    if filters.created_before:
        query = query.filter(AuditLog.created_at <= filters.created_before)
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply sorting
    sort_column = getattr(AuditLog, filters.sort_by, AuditLog.created_at)
    if filters.sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    
    # Apply pagination
    logs = query.offset(filters.skip).limit(filters.limit).all()
    
    # Calculate pagination info
    page = (filters.skip // filters.limit) + 1
    has_next = (filters.skip + filters.limit) < total_count
    has_previous = filters.skip > 0
    
    return AuditLogSearchResult(
        logs=logs,
        total_count=total_count,
        page=page,
        page_size=filters.limit,
        has_next=has_next,
        has_previous=has_previous
    )


def get_security_events(
    db: Session,
    limit: int = 100,
    severity_level: Optional[SeverityLevel] = None
) -> List[AuditLog]:
    """
    Get recent security events.
    
    Args:
        db: Database session
        limit: Maximum number of events to return
        severity_level: Filter by severity level
        
    Returns:
        List of security event audit logs
    """
    query = db.query(AuditLog).filter(AuditLog.is_security_event.isnot(None))
    
    if severity_level:
        query = query.filter(AuditLog.severity_level == severity_level.value)
    
    return query.order_by(desc(AuditLog.created_at)).limit(limit).all()


def get_user_audit_logs(
    db: Session,
    user_id: int,
    limit: int = 50
) -> List[AuditLog]:
    """
    Get audit logs for a specific user.
    
    Args:
        db: Database session
        user_id: ID of the user
        limit: Maximum number of logs to return
        
    Returns:
        List of audit logs for the user
    """
    return (
        db.query(AuditLog)
        .filter(
            or_(
                AuditLog.user_id == user_id,  # Actions performed by the user
                AuditLog.resource_id == str(user_id)  # Actions performed on the user
            )
        )
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
        .all()
    )


def get_recent_audit_logs(
    db: Session,
    hours: int = 24,
    limit: int = 100
) -> List[AuditLog]:
    """
    Get recent audit logs within the specified time window.
    
    Args:
        db: Database session
        hours: Number of hours to look back
        limit: Maximum number of logs to return
        
    Returns:
        List of recent audit logs
    """
    cutoff_time = datetime.now(timezone.utc) - timezone.timedelta(hours=hours)
    
    return (
        db.query(AuditLog)
        .filter(AuditLog.created_at >= cutoff_time)
        .order_by(desc(AuditLog.created_at))
        .limit(limit)
        .all()
    )
