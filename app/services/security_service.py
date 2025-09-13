"""
Security service for rate limiting, failed login tracking, and security monitoring.
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
import time
import hashlib
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditAction, SecurityEventType, SeverityLevel, AuditStatus
from app.services.audit_service import log_security_event


class RateLimiter:
    """Simple in-memory rate limiter using sliding window algorithm."""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)  # key -> deque of timestamps
    
    def is_allowed(self, key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed for the given key.
        
        Args:
            key: Unique identifier (e.g., IP address, user_id)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        user_requests = self.requests[key]
        while user_requests and user_requests[0] < window_start:
            user_requests.popleft()
        
        # Check if under limit
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            remaining = self.max_requests - len(user_requests)
            reset_time = datetime.fromtimestamp(now + self.window_seconds, tz=timezone.utc)
            
            return True, {
                "limit": self.max_requests,
                "remaining": remaining,
                "reset_time": reset_time,
                "retry_after": None
            }
        else:
            # Rate limit exceeded
            oldest_request = user_requests[0]
            retry_after = int(oldest_request + self.window_seconds - now)
            reset_time = datetime.fromtimestamp(oldest_request + self.window_seconds, tz=timezone.utc)
            
            return False, {
                "limit": self.max_requests,
                "remaining": 0,
                "reset_time": reset_time,
                "retry_after": retry_after
            }
    
    def get_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get current rate limit information for a key."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        user_requests = self.requests[key]
        while user_requests and user_requests[0] < window_start:
            user_requests.popleft()
        
        remaining = max(0, self.max_requests - len(user_requests))
        reset_time = datetime.fromtimestamp(now + self.window_seconds, tz=timezone.utc)
        
        return {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset_time": reset_time,
            "retry_after": None
        }


class FailedLoginTracker:
    """Track failed login attempts for security monitoring."""
    
    def __init__(self, max_attempts: int = 5, lockout_duration_minutes: int = 30):
        """
        Initialize failed login tracker.
        
        Args:
            max_attempts: Maximum failed attempts before lockout
            lockout_duration_minutes: Duration of account lockout in minutes
        """
        self.max_attempts = max_attempts
        self.lockout_duration = timedelta(minutes=lockout_duration_minutes)
        self.failed_attempts = defaultdict(list)  # username -> list of attempt times
        self.locked_accounts = {}  # username -> lockout end time
    
    def record_failed_attempt(self, username: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Record a failed login attempt.
        
        Args:
            username: Username that failed to login
            ip_address: IP address of the attempt
            
        Returns:
            Dictionary with attempt information and lockout status
        """
        now = datetime.now(timezone.utc)
        
        # Clean old attempts (older than lockout duration)
        cutoff_time = now - self.lockout_duration
        attempts = self.failed_attempts[username]
        attempts[:] = [attempt_time for attempt_time in attempts if attempt_time > cutoff_time]
        
        # Add new attempt
        attempts.append(now)
        
        # Check if account should be locked
        is_locked = len(attempts) >= self.max_attempts
        if is_locked:
            self.locked_accounts[username] = now + self.lockout_duration
        
        return {
            "username": username,
            "attempt_count": len(attempts),
            "is_locked": is_locked,
            "lockout_until": self.locked_accounts.get(username),
            "next_allowed_attempt": cutoff_time + self.lockout_duration if len(attempts) > 0 else None,
            "ip_address": ip_address
        }
    
    def is_account_locked(self, username: str) -> Tuple[bool, Optional[datetime]]:
        """
        Check if an account is currently locked.
        
        Args:
            username: Username to check
            
        Returns:
            Tuple of (is_locked, lockout_until)
        """
        lockout_until = self.locked_accounts.get(username)
        if lockout_until and lockout_until > datetime.now(timezone.utc):
            return True, lockout_until
        
        # Remove expired lockout
        if lockout_until:
            del self.locked_accounts[username]
        
        return False, None
    
    def clear_failed_attempts(self, username: str):
        """Clear failed attempts for a user (e.g., after successful login)."""
        if username in self.failed_attempts:
            del self.failed_attempts[username]
        if username in self.locked_accounts:
            del self.locked_accounts[username]


# Global instances
admin_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)  # 30 requests per minute
auth_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)   # 10 login attempts per minute
failed_login_tracker = FailedLoginTracker(max_attempts=5, lockout_duration_minutes=30)


class SecurityService:
    """Main security service for monitoring and enforcement."""
    
    @staticmethod
    def check_rate_limit(
        endpoint: str,
        identifier: str,
        db: Session,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check rate limit for an endpoint.
        
        Args:
            endpoint: API endpoint being accessed
            identifier: Unique identifier (IP address or user_id)
            db: Database session for logging
            ip_address: IP address for logging
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        # Choose appropriate rate limiter
        if endpoint.startswith("/api/admin") or endpoint.startswith("/api/users"):
            rate_limiter = admin_rate_limiter
        elif endpoint.startswith("/api/auth"):
            rate_limiter = auth_rate_limiter
        else:
            # Default rate limiter for other endpoints
            rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
        
        is_allowed, rate_info = rate_limiter.is_allowed(identifier)
        
        # Log rate limit events
        if not is_allowed:
            log_security_event(
                db=db,
                action=AuditAction.RATE_LIMIT_EXCEEDED,
                description=f"Rate limit exceeded for {endpoint}",
                severity_level=SeverityLevel.WARNING,
                ip_address=ip_address,
                request_path=endpoint,
                details={
                    "identifier": identifier,
                    "rate_limit_info": rate_info
                },
                is_security_event=SecurityEventType.SUSPICIOUS
            )
        
        return is_allowed, rate_info
    
    @staticmethod
    def check_failed_login_attempts(
        username: str,
        db: Session,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[datetime], Dict[str, Any]]:
        """
        Check failed login attempts for a user.
        
        Args:
            username: Username to check
            db: Database session for logging
            ip_address: IP address of the attempt
            
        Returns:
            Tuple of (is_allowed, lockout_until, attempt_info)
        """
        # Check if account is currently locked
        is_locked, lockout_until = failed_login_tracker.is_account_locked(username)
        
        if is_locked:
            # Log security event for locked account access attempt
            log_security_event(
                db=db,
                action=AuditAction.ACCOUNT_LOCKOUT,
                description=f"Login attempt on locked account '{username}'",
                severity_level=SeverityLevel.WARNING,
                username=username,
                ip_address=ip_address,
                details={
                    "lockout_until": lockout_until.isoformat() if lockout_until else None
                },
                is_security_event=SecurityEventType.SUSPICIOUS
            )
        
        attempt_info = failed_login_tracker.record_failed_attempt(username, ip_address)
        return not is_locked, lockout_until, attempt_info
    
    @staticmethod
    def record_successful_login(username: str, user_id: int, db: Session, ip_address: Optional[str] = None):
        """
        Record a successful login and clear failed attempts.
        
        Args:
            username: Username that successfully logged in
            user_id: ID of the user
            db: Database session for logging
            ip_address: IP address of the login
        """
        # Clear failed attempts
        failed_login_tracker.clear_failed_attempts(username)
        
        # Log successful login
        from app.services.audit_service import log_authentication_event
        log_authentication_event(
            db=db,
            action=AuditAction.LOGIN_SUCCESS,
            username=username,
            user_id=user_id,
            ip_address=ip_address,
            status=AuditStatus.SUCCESS
        )
    
    @staticmethod
    def record_failed_login(
        username: str,
        db: Session,
        ip_address: Optional[str] = None,
        error_reason: str = "invalid_credentials"
    ):
        """
        Record a failed login attempt.
        
        Args:
            username: Username that failed to login
            db: Database session for logging
            ip_address: IP address of the attempt
            error_reason: Reason for the failure
        """
        # Record the failed attempt
        attempt_info = SecurityService.check_failed_login_attempts(username, db, ip_address)
        
        # Log the failed login
        from app.services.audit_service import log_authentication_event
        log_authentication_event(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            username=username,
            ip_address=ip_address,
            details={
                "error_reason": error_reason,
                "attempt_info": attempt_info[2]
            },
            status=AuditStatus.FAILED,
            error_message=f"Login failed: {error_reason}",
            is_security_event=SecurityEventType.SUSPICIOUS if attempt_info[2]["attempt_count"] > 3 else None
        )
    
    @staticmethod
    def detect_suspicious_activity(
        db: Session,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        activity_type: str = "unknown",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Detect and log suspicious activity.
        
        Args:
            db: Database session for logging
            user_id: ID of user involved
            username: Username of user involved
            ip_address: IP address of the activity
            activity_type: Type of suspicious activity
            details: Additional details about the activity
        """
        log_security_event(
            db=db,
            action=AuditAction.SUSPICIOUS_ACTIVITY,
            description=f"Suspicious activity detected: {activity_type}",
            severity_level=SeverityLevel.WARNING,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details,
            is_security_event=SecurityEventType.SUSPICIOUS
        )
    
    @staticmethod
    def get_security_summary(db: Session, hours: int = 24) -> Dict[str, Any]:
        """
        Get a summary of recent security events.
        
        Args:
            db: Database session
            hours: Number of hours to look back
            
        Returns:
            Dictionary with security summary
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Count different types of security events
        security_events = (
            db.query(AuditLog)
            .filter(
                and_(
                    AuditLog.is_security_event.isnot(None),
                    AuditLog.created_at >= cutoff_time
                )
            )
            .all()
        )
        
        # Count by type
        event_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in security_events:
            event_counts[event.action] += 1
            severity_counts[event.severity_level] += 1
        
        # Count failed logins
        failed_logins = len([
            event for event in security_events
            if event.action == AuditAction.LOGIN_FAILED.value
        ])
        
        # Count rate limit violations
        rate_limit_violations = len([
            event for event in security_events
            if event.action == AuditAction.RATE_LIMIT_EXCEEDED.value
        ])
        
        return {
            "time_window_hours": hours,
            "total_security_events": len(security_events),
            "failed_logins": failed_logins,
            "rate_limit_violations": rate_limit_violations,
            "event_types": dict(event_counts),
            "severity_distribution": dict(severity_counts),
            "recent_events": [
                {
                    "id": event.id,
                    "action": event.action,
                    "description": event.description,
                    "severity": event.severity_level,
                    "created_at": event.created_at.isoformat()
                }
                for event in security_events[:10]  # Last 10 events
            ]
        }
