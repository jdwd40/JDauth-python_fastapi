"""
Audit middleware for automatic logging of admin actions and security events.
"""

from typing import Callable, Optional
from datetime import datetime
import logging

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.audit_service import log_audit_event
from app.services.security_service import SecurityService
from app.schemas.audit import AuditAction, AuditStatus, SeverityLevel, SecurityEventType

logger = logging.getLogger(__name__)


class AuditMiddleware:
    """Middleware for automatic audit logging of admin actions."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        response = await self._process_request(request)
        
        if response:
            # Return the response immediately (e.g., rate limited)
            await response(scope, receive, send)
            return
        
        # Continue with normal request processing
        await self.app(scope, receive, send)
    
    async def _process_request(self, request: Request) -> Optional[Callable]:
        """
        Process the request for audit logging and security checks.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Response function if request should be blocked, None otherwise
        """
        # Skip non-API requests
        if not request.url.path.startswith("/api"):
            return None
        
        # Get database session
        db = next(get_db())
        
        try:
            # Extract request information
            ip_address = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent")
            method = request.method
            path = request.url.path
            
            # Check rate limiting
            is_allowed, rate_info = SecurityService.check_rate_limit(
                endpoint=path,
                identifier=ip_address,
                db=db,
                ip_address=ip_address
            )
            
            if not is_allowed:
                # Return rate limit response
                return lambda scope, receive, send: self._rate_limit_response(rate_info, scope, receive, send)
            
            # For admin endpoints, we'll log the action after processing
            # This is handled by the audit dependency in the route handlers
            
        except Exception as e:
            logger.error(f"Audit middleware error: {e}")
        finally:
            db.close()
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    async def _rate_limit_response(self, rate_info: dict, scope, receive, send):
        """Send rate limit exceeded response."""
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": True,
                "message": "Rate limit exceeded",
                "status_code": 429,
                "rate_limit": rate_info,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={
                "Retry-After": str(rate_info.get("retry_after", 60)),
                "X-RateLimit-Limit": str(rate_info.get("limit", 30)),
                "X-RateLimit-Remaining": str(rate_info.get("remaining", 0)),
                "X-RateLimit-Reset": str(int(rate_info.get("reset_time", datetime.now()).timestamp()))
            }
        )
        await response(scope, receive, send)


def audit_admin_action(
    action: AuditAction,
    resource_type: str = "user",
    resource_id: Optional[str] = None,
    description: Optional[str] = None,
    details: Optional[dict] = None
):
    """
    FastAPI dependency for logging admin actions.
    
    This dependency should be used in admin route handlers to automatically
    log the action being performed.
    
    Args:
        action: The audit action being performed
        resource_type: Type of resource being affected
        resource_id: ID of the resource being affected
        description: Custom description (auto-generated if not provided)
        details: Additional details to log
        
    Returns:
        Function that logs the action and returns None
    """
    def _log_action(
        request: Request,
        current_user,
        db: Session = next(get_db())
    ):
        try:
            # Extract request information
            ip_address = _get_client_ip(request)
            user_agent = request.headers.get("user-agent")
            
            # Auto-generate description if not provided
            if not description:
                auto_description = f"Admin {current_user.username} performed {action.value}"
                if resource_id:
                    auto_description += f" on {resource_type} {resource_id}"
            else:
                auto_description = description
            
            # Log the action
            log_audit_event(
                db=db,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=current_user.id,
                username=current_user.username,
                description=auto_description,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request.method,
                request_path=request.url.path,
                details=details,
                status=AuditStatus.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Failed to log admin action: {e}")
        finally:
            db.close()
        
        return None
    
    return _log_action


def audit_user_management_action(
    action: AuditAction,
    target_user_id: Optional[int] = None,
    target_username: Optional[str] = None,
    description: Optional[str] = None,
    details: Optional[dict] = None
):
    """
    FastAPI dependency specifically for user management actions.
    
    Args:
        action: The user management action
        target_user_id: ID of user being affected
        target_username: Username of user being affected
        description: Custom description
        details: Additional details
        
    Returns:
        Function that logs the user management action
    """
    def _log_user_action(
        request: Request,
        current_user,
        db: Session = next(get_db())
    ):
        try:
            # Extract request information
            ip_address = _get_client_ip(request)
            user_agent = request.headers.get("user-agent")
            
            # Log the user management action
            log_user_action(
                db=db,
                action=action,
                user_id=current_user.id,
                username=current_user.username,
                target_user_id=target_user_id,
                target_username=target_username,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request.method,
                request_path=request.url.path,
                details=details,
                status=AuditStatus.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Failed to log user management action: {e}")
        finally:
            db.close()
        
        return None
    
    return _log_user_action


def _get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded headers first
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return "unknown"


# Middleware for automatic security event detection
class SecurityEventDetector:
    """Middleware for detecting and logging security events."""
    
    @staticmethod
    def detect_suspicious_patterns(request: Request, response: Response) -> Optional[dict]:
        """
        Detect suspicious patterns in requests and responses.
        
        Args:
            request: FastAPI request object
            response: FastAPI response object
            
        Returns:
            Security event details if detected, None otherwise
        """
        suspicious_indicators = []
        
        # Check for suspicious headers
        suspicious_headers = [
            "x-forwarded-for",  # Potential IP spoofing
            "x-real-ip",
            "x-cluster-client-ip"
        ]
        
        for header in suspicious_headers:
            if header in request.headers:
                # Multiple IPs in forwarded header could indicate proxy chaining
                value = request.headers[header]
                if "," in value and len(value.split(",")) > 3:
                    suspicious_indicators.append(f"Multiple IPs in {header}: {value}")
        
        # Check for unusual user agents
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or len(user_agent) < 10:
            suspicious_indicators.append("Missing or suspicious user agent")
        
        # Check for SQL injection patterns (basic detection)
        query_params = str(request.query_params).lower()
        sql_patterns = ["union", "select", "insert", "update", "delete", "drop", "exec"]
        for pattern in sql_patterns:
            if pattern in query_params:
                suspicious_indicators.append(f"Potential SQL injection pattern: {pattern}")
        
        # Check for path traversal attempts
        path = request.url.path
        if "../" in path or "..\\" in path:
            suspicious_indicators.append("Potential path traversal attempt")
        
        # Check for unusual response codes
        if response.status_code in [500, 502, 503, 504]:
            suspicious_indicators.append(f"Server error response: {response.status_code}")
        
        if suspicious_indicators:
            return {
                "indicators": suspicious_indicators,
                "ip_address": _get_client_ip(request),
                "user_agent": user_agent,
                "path": path,
                "method": request.method,
                "status_code": response.status_code
            }
        
        return None
