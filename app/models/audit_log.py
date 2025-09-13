"""
Audit log model for tracking administrative actions and security events.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.config.database import Base


class AuditLog(Base):
    """Audit log model for tracking administrative actions and security events."""
    
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # e.g., "CREATE_USER", "UPDATE_USER"
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., "user", "role"
    resource_id = Column(String(50), nullable=True, index=True)  # ID of the affected resource
    
    # User information
    user_id = Column(Integer, nullable=True, index=True)  # ID of user performing the action
    username = Column(String(50), nullable=True, index=True)  # Username for easier querying
    
    # Request details
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6 address
    user_agent = Column(Text, nullable=True)  # Browser/client information
    request_method = Column(String(10), nullable=True)  # HTTP method (GET, POST, etc.)
    request_path = Column(String(500), nullable=True)  # API endpoint path
    
    # Action details
    description = Column(Text, nullable=False)  # Human-readable description
    details = Column(JSON, nullable=True)  # Additional structured data
    
    # Result information
    status = Column(String(20), nullable=False, default="success", index=True)  # success, failed, error
    error_message = Column(Text, nullable=True)  # Error details if action failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Security event flags
    is_security_event = Column(String(20), nullable=True, index=True)  # null, "suspicious", "critical"
    severity_level = Column(String(20), nullable=True, default="info", index=True)  # info, warning, error, critical

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id}, status='{self.status}')>"
    
    def to_dict(self):
        """Convert audit log to dictionary for API responses."""
        return {
            "id": self.id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "request_method": self.request_method,
            "request_path": self.request_path,
            "description": self.description,
            "details": self.details,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_security_event": self.is_security_event,
            "severity_level": self.severity_level
        }
