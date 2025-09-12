"""
Authentication service for handling user authentication, JWT tokens, and security operations.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.models.user import User
from app.config.settings import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password
    
    Returns:
        User instance if authentication successful, None otherwise
    """
    # Handle empty credentials
    if not username or not password:
        return None
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    
    # Verify password
    if not _verify_password(password, user.hashed_password):
        return None
    
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
