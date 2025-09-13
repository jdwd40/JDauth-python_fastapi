# LLM Task 4: Security & Audit System

## 🎯 **Task Overview**
Implement comprehensive security enhancements and audit logging system for admin operations. This includes audit trails, enhanced security measures, and monitoring capabilities.

## 📋 **Context: Security & Accountability**
After implementing admin CRUD, role management, and enhanced features, you need:
- **Audit Logging**: Track all admin actions for accountability
- **Enhanced Security**: Rate limiting, session management, IP restrictions
- **Monitoring**: Security event detection and logging
- **Compliance**: Prepare for production security requirements

**Prerequisites**: Tasks 1, 2, and 3 must be completed first.

## 🏗️ **Current Security State**
- ✅ JWT-based authentication
- ✅ Role-based authorization
- ✅ Password hashing with bcrypt
- ✅ Basic input validation
- ❌ No audit logging
- ❌ No rate limiting
- ❌ No security monitoring
- ❌ No session management

## 🎯 **Your Specific Tasks**

### **Task 4A: Audit Logging System**

#### **4A.1: Audit Log Database Model**
- [ ] **Create `app/models/audit_log.py`**:
  ```python
  class AuditLog(Base):
      __tablename__ = "audit_logs"
      
      id = Column(Integer, primary_key=True, index=True)
      admin_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
      action = Column(String(50), nullable=False)  # "CREATE_USER", "DELETE_USER", etc.
      target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
      target_resource = Column(String(50), nullable=True)  # "user", "system", etc.
      details = Column(JSON, nullable=True)  # Additional context
      ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
      user_agent = Column(String(500), nullable=True)
      timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
      
      # Relationships
      admin_user = relationship("User", foreign_keys=[admin_user_id])
      target_user = relationship("User", foreign_keys=[target_user_id])
  ```

#### **4A.2: Audit Service**
- [ ] **Create `app/services/audit_service.py`**:
  ```python
  from enum import Enum
  
  class AuditAction(str, Enum):
      # User management actions
      CREATE_USER = "CREATE_USER"
      UPDATE_USER = "UPDATE_USER"
      DELETE_USER = "DELETE_USER"
      ACTIVATE_USER = "ACTIVATE_USER"
      DEACTIVATE_USER = "DEACTIVATE_USER"
      CHANGE_USER_ROLE = "CHANGE_USER_ROLE"
      
      # Bulk actions
      BULK_ACTIVATE_USERS = "BULK_ACTIVATE_USERS"
      BULK_DEACTIVATE_USERS = "BULK_DEACTIVATE_USERS"
      
      # System actions
      ADMIN_LOGIN = "ADMIN_LOGIN"
      EXPORT_USERS = "EXPORT_USERS"
      VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"
  
  def log_admin_action(
      db: Session,
      admin_user_id: int,
      action: AuditAction,
      target_user_id: Optional[int] = None,
      details: Optional[Dict[str, Any]] = None,
      ip_address: Optional[str] = None,
      user_agent: Optional[str] = None
  ) -> AuditLog:
      """Log an admin action for audit trail."""
  
  def get_audit_logs(
      db: Session,
      admin_user_id: Optional[int] = None,
      action: Optional[AuditAction] = None,
      target_user_id: Optional[int] = None,
      start_date: Optional[datetime] = None,
      end_date: Optional[datetime] = None,
      skip: int = 0,
      limit: int = 100
  ) -> List[AuditLog]:
      """Retrieve audit logs with filtering."""
  ```

#### **4A.3: Audit Middleware**
- [ ] **Create `app/middleware/audit_middleware.py`**:
  ```python
  from fastapi import Request
  import json
  
  async def audit_middleware(request: Request, call_next):
      """Middleware to automatically log admin actions."""
      
      # Check if this is an admin endpoint
      if request.url.path.startswith("/api/admin/"):
          # Extract user info from JWT
          # Log the action after successful response
          pass
      
      response = await call_next(request)
      return response
  ```

#### **4A.4: Audit Log Endpoints**
- [ ] **Add to `app/routes/user.py`** (admin_router):
  ```python
  @admin_router.get("/admin/audit-logs", response_model=List[AuditLogResponse])
  def get_audit_logs(
      action: Optional[AuditAction] = Query(None),
      target_user_id: Optional[int] = Query(None),
      start_date: Optional[datetime] = Query(None),
      end_date: Optional[datetime] = Query(None),
      skip: int = Query(0, ge=0),
      limit: int = Query(50, ge=1, le=100),
      current_user: User = Depends(require_admin),
      db: Session = Depends(get_db)
  ):
  ```

### **Task 4B: Enhanced Security Measures**

#### **4B.1: Rate Limiting**
- [ ] **Install slowapi**: `pip install slowapi`
- [ ] **Create `app/middleware/rate_limit.py`**:
  ```python
  from slowapi import Limiter, _rate_limit_exceeded_handler
  from slowapi.util import get_remote_address
  from slowapi.errors import RateLimitExceeded
  
  limiter = Limiter(key_func=get_remote_address)
  
  # Different limits for different endpoint types
  ADMIN_RATE_LIMIT = "30/minute"  # Admin endpoints
  AUTH_RATE_LIMIT = "10/minute"   # Login attempts
  GENERAL_RATE_LIMIT = "100/minute"  # General API
  ```
- [ ] **Apply to Admin Endpoints**: Add rate limiting decorators
- [ ] **Apply to Auth Endpoints**: Prevent brute force attacks

#### **4B.2: Enhanced Session Management**
- [ ] **Session Tracking Model**:
  ```python
  class UserSession(Base):
      __tablename__ = "user_sessions"
      
      id = Column(String(128), primary_key=True)  # Session ID
      user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
      ip_address = Column(String(45), nullable=False)
      user_agent = Column(String(500), nullable=True)
      created_at = Column(DateTime(timezone=True), server_default=func.now())
      last_activity = Column(DateTime(timezone=True), server_default=func.now())
      expires_at = Column(DateTime(timezone=True), nullable=False)
      is_active = Column(Boolean, default=True)
      
      user = relationship("User")
  ```
- [ ] **Session Service**: Create, validate, invalidate sessions
- [ ] **Admin Session Monitoring**: Track admin sessions separately

#### **4B.3: Security Headers & CORS**
- [ ] **Update `app/main.py`** with security headers:
  ```python
  from fastapi.middleware.trustedhost import TrustedHostMiddleware
  from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
  
  # Security headers middleware
  @app.middleware("http")
  async def add_security_headers(request: Request, call_next):
      response = await call_next(request)
      response.headers["X-Content-Type-Options"] = "nosniff"
      response.headers["X-Frame-Options"] = "DENY"
      response.headers["X-XSS-Protection"] = "1; mode=block"
      response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
      return response
  ```

#### **4B.4: Input Sanitization & Validation**
- [ ] **Enhanced Validators**: Create custom Pydantic validators
- [ ] **SQL Injection Prevention**: Parameterized queries (already using SQLAlchemy)
- [ ] **XSS Prevention**: Input sanitization for text fields
- [ ] **File Upload Security**: If implementing file uploads

### **Task 4C: Security Monitoring & Alerts**

#### **4C.1: Security Event Detection**
- [ ] **Create `app/services/security_service.py`**:
  ```python
  class SecurityEvent(str, Enum):
      MULTIPLE_FAILED_LOGINS = "MULTIPLE_FAILED_LOGINS"
      ADMIN_ROLE_CHANGE = "ADMIN_ROLE_CHANGE"
      BULK_USER_DELETION = "BULK_USER_DELETION"
      SUSPICIOUS_IP_ACCESS = "SUSPICIOUS_IP_ACCESS"
      UNUSUAL_ADMIN_ACTIVITY = "UNUSUAL_ADMIN_ACTIVITY"
  
  def detect_security_events(db: Session) -> List[Dict[str, Any]]:
      """Analyze recent activity for security events."""
  
  def log_security_event(
      db: Session,
      event_type: SecurityEvent,
      details: Dict[str, Any],
      severity: str = "medium"
  ):
      """Log a security event for monitoring."""
  ```

#### **4C.2: Failed Login Tracking**
- [ ] **Login Attempt Model**:
  ```python
  class LoginAttempt(Base):
      __tablename__ = "login_attempts"
      
      id = Column(Integer, primary_key=True)
      username = Column(String(50), nullable=False)
      ip_address = Column(String(45), nullable=False)
      success = Column(Boolean, nullable=False)
      timestamp = Column(DateTime(timezone=True), server_default=func.now())
      user_agent = Column(String(500), nullable=True)
  ```
- [ ] **Track in Auth Service**: Log all login attempts
- [ ] **Account Lockout**: Temporary lockout after failed attempts

#### **4C.3: Monitoring Dashboard**
- [ ] **Security Dashboard Endpoint**: `GET /admin/security/dashboard`
- [ ] **Metrics to Track**:
  ```python
  {
      "failed_logins_24h": 15,
      "admin_actions_24h": 42,
      "security_events": [
          {"type": "MULTIPLE_FAILED_LOGINS", "count": 3, "last_occurrence": "..."},
      ],
      "active_admin_sessions": 2,
      "suspicious_ips": ["192.168.1.100"],
      "recent_role_changes": 1
  }
  ```

### **Task 4D: Compliance & Documentation**

#### **4D.1: Data Privacy Compliance**
- [ ] **User Data Export**: GDPR-style data export for users
- [ ] **User Data Deletion**: Complete user data removal
- [ ] **Data Retention Policies**: Configurable audit log retention
- [ ] **Privacy Controls**: User consent tracking (if needed)

#### **4D.2: Security Documentation**
- [ ] **Create `docs/security.md`**: Security implementation guide
- [ ] **Audit Log Schema**: Document all audit actions
- [ ] **Security Configuration**: Document security settings
- [ ] **Incident Response**: Basic incident response procedures

## 💡 **Key Implementation Details**

### **1. Audit Logging Integration**
```python
# Decorator for automatic audit logging
def audit_action(action: AuditAction, target_field: str = None):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract admin user and target from function params
            admin_user = kwargs.get('current_user')
            target_id = kwargs.get(target_field) if target_field else None
            
            try:
                result = await func(*args, **kwargs)
                
                # Log successful action
                audit_service.log_admin_action(
                    db=kwargs.get('db'),
                    admin_user_id=admin_user.id,
                    action=action,
                    target_user_id=target_id,
                    details={"success": True}
                )
                
                return result
            except Exception as e:
                # Log failed action
                audit_service.log_admin_action(
                    db=kwargs.get('db'),
                    admin_user_id=admin_user.id,
                    action=action,
                    target_user_id=target_id,
                    details={"success": False, "error": str(e)}
                )
                raise
        return wrapper
    return decorator
```

### **2. Rate Limiting Implementation**
```python
# Apply to admin endpoints
@admin_router.post("/admin/users")
@limiter.limit(ADMIN_RATE_LIMIT)
async def create_user_as_admin(request: Request, ...):
    # Implementation
    pass

# Apply to auth endpoints
@auth_router.post("/login")
@limiter.limit(AUTH_RATE_LIMIT)
async def login(request: Request, ...):
    # Implementation
    pass
```

### **3. Security Event Detection**
```python
def detect_multiple_failed_logins(db: Session) -> List[Dict]:
    """Detect multiple failed login attempts from same IP."""
    recent_failures = db.query(LoginAttempt).filter(
        LoginAttempt.success == False,
        LoginAttempt.timestamp >= datetime.now() - timedelta(hours=1)
    ).all()
    
    # Group by IP and count failures
    ip_failures = {}
    for attempt in recent_failures:
        ip_failures[attempt.ip_address] = ip_failures.get(attempt.ip_address, 0) + 1
    
    # Return IPs with > 5 failures
    return [{"ip": ip, "failures": count} 
            for ip, count in ip_failures.items() if count > 5]
```

## 📋 **New Schemas Needed**

### **Create `app/schemas/audit.py`**
```python
class AuditLogResponse(BaseModel):
    id: int
    admin_username: str
    action: AuditAction
    target_username: Optional[str] = None
    target_resource: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    timestamp: datetime

class SecurityDashboardResponse(BaseModel):
    failed_logins_24h: int
    admin_actions_24h: int
    security_events: List[Dict[str, Any]]
    active_admin_sessions: int
    recent_role_changes: int

class LoginAttemptResponse(BaseModel):
    username: str
    ip_address: str
    success: bool
    timestamp: datetime
```

## 🧪 **Testing Strategy**

### **Test Categories**
1. **Audit Logging Tests**: Verify all actions are logged
2. **Rate Limiting Tests**: Test rate limit enforcement
3. **Security Event Tests**: Test event detection logic
4. **Session Management Tests**: Test session lifecycle
5. **Security Header Tests**: Verify security headers
6. **Failed Login Tests**: Test login attempt tracking

### **Key Test Cases**
```python
def test_admin_action_creates_audit_log(self, admin_client):
    """Test that admin actions create audit logs."""

def test_rate_limiting_blocks_excessive_requests(self, client):
    """Test rate limiting blocks too many requests."""

def test_failed_login_tracking(self, client):
    """Test failed login attempts are tracked."""

def test_security_event_detection(self, admin_client):
    """Test security events are detected."""

def test_audit_log_filtering(self, admin_client):
    """Test audit log filtering and pagination."""
```

## 📁 **Files You'll Need to Create/Modify**

### **New Files**
- `app/models/audit_log.py` - Audit log model
- `app/models/user_session.py` - Session tracking model  
- `app/models/login_attempt.py` - Login attempt tracking
- `app/services/audit_service.py` - Audit logging service
- `app/services/security_service.py` - Security monitoring
- `app/middleware/audit_middleware.py` - Audit middleware
- `app/middleware/rate_limit.py` - Rate limiting
- `app/schemas/audit.py` - Audit schemas
- `docs/security.md` - Security documentation

### **Modified Files**
- `app/main.py` - Add middleware and security headers
- `app/routes/user.py` - Add audit endpoints, rate limiting
- `app/routes/auth.py` - Add login attempt tracking
- `app/services/auth_service.py` - Integrate session tracking
- Database migration files - Add new tables

## 🎯 **Success Criteria**
- [ ] All admin actions are automatically logged
- [ ] Rate limiting prevents abuse
- [ ] Security events are detected and logged
- [ ] Failed login attempts are tracked
- [ ] Admin can view audit logs with filtering
- [ ] Security dashboard shows relevant metrics
- [ ] Session management is secure
- [ ] Security headers are properly set
- [ ] Comprehensive test coverage
- [ ] Security documentation is complete

## 🚀 **Expected Outcome**
After this task, the system will have:
- **Complete audit trail** of all admin actions
- **Enhanced security** against common attacks
- **Monitoring capabilities** for suspicious activity
- **Compliance readiness** for production deployment
- **Security dashboard** for administrators
- **Professional-grade security** measures

## 📚 **Context Files to Reference**
- Previous task implementations (Tasks 1, 2, 3)
- `app/main.py` - Current middleware setup
- `app/routes/auth.py` - Current auth implementation
- `app/services/auth_service.py` - Current auth service

## ⏱️ **Estimated Time**: 10-12 hours
- 4 hours: Audit logging system
- 3 hours: Security enhancements (rate limiting, headers)
- 2 hours: Security monitoring and event detection
- 3 hours: Testing and documentation
