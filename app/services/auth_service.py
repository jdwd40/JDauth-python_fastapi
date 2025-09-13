"""
Authentication service for handling user authentication, JWT tokens, and security operations.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.models.user import User
from app.config.settings import settings
from app.utils.security import verify_password

# JWT settings (imported from utils.security)
from app.utils.security import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def authenticate_user(db: Session, username: str, password: str, ip_address: Optional[str] = None) -> Optional[User]:
    """
    Authenticate a user with username and password.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password
        ip_address: IP address of the login attempt (for security tracking)
    
    Returns:
        User instance if authentication successful, None otherwise
    """
    # Handle empty credentials
    if not username or not password:
        if username:
            # Log failed login attempt for empty password
            from app.services.security_service import SecurityService
            SecurityService.record_failed_login(username, db, ip_address, "empty_password")
        return None
    
    # Check if account is locked
    from app.services.security_service import failed_login_tracker
    is_locked, lockout_until = failed_login_tracker.is_account_locked(username)
    if is_locked:
        from app.services.security_service import SecurityService
        SecurityService.record_failed_login(username, db, ip_address, "account_locked")
        return None
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if not user:
        from app.services.security_service import SecurityService
        SecurityService.record_failed_login(username, db, ip_address, "user_not_found")
        return None
    
    # Check if user is active
    if not user.is_active:
        from app.services.security_service import SecurityService
        SecurityService.record_failed_login(username, db, ip_address, "account_inactive")
        return None
    
    # Verify password
    if not verify_password(password, user.hashed_password):
        from app.services.security_service import SecurityService
        SecurityService.record_failed_login(username, db, ip_address, "invalid_password")
        return None
    
    # Successful authentication - clear failed attempts and log success
    from app.services.security_service import SecurityService
    SecurityService.record_successful_login(username, user.id, db, ip_address)
    
    return user


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time delta
    
    Returns:
        JWT token string
    
    Raises:
        ValueError: If data is empty or invalid
    """
    if not data:
        raise ValueError("Token data cannot be empty")
    
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Create JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload
    
    Raises:
        ValueError: If token is invalid or expired
    """
    if not token:
        raise ValueError("Invalid token")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except JWTError:
        raise ValueError("Invalid token")


def get_current_user_from_token(db: Session, token: str) -> User:
    """
    Get the current user from a JWT token.
    
    Args:
        db: Database session
        token: JWT token string
    
    Returns:
        User instance
    
    Raises:
        ValueError: If token is invalid, expired, or user not found
    """
    # Verify and decode token
    payload = verify_token(token)
    
    # Extract username from token
    username = payload.get("sub")
    if not username:
        raise ValueError("Invalid token payload")
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("User not found")
    
    return user
