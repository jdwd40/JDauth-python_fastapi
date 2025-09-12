"""
User service for handling user-related business logic and data operations.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import get_password_hash


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user_data: User creation data
    
    Returns:
        Created User instance
    
    Raises:
        ValueError: If username already exists or invalid data
    """
    # Validate input data
    if not user_data.username or len(user_data.username.strip()) == 0:
        raise ValueError("Username cannot be empty")
    
    if not user_data.password or len(user_data.password) < 6:
        raise ValueError("Password must be at least 6 characters")
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise ValueError("Username already exists")
    
    # Create new user with hashed password
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Username already exists")


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username.
    
    Args:
        db: Database session
        username: Username to search for
    
    Returns:
        User instance if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: User ID to search for
    
    Returns:
        User instance if found, None otherwise
    
    Raises:
        ValueError: If user_id is invalid
    """
    if user_id <= 0:
        raise ValueError("User ID must be positive")
    
    return db.query(User).filter(User.id == user_id).first()


def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
    """
    Update a user's information.
    
    Args:
        db: Database session
        user_id: ID of user to update
        user_data: Update data
    
    Returns:
        Updated User instance
    
    Raises:
        ValueError: If user not found or username already exists
    """
    # Get existing user
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")
    
    # Check if new username already exists (if username is being changed)
    if user_data.username and user_data.username != db_user.username:
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise ValueError("Username already exists")
    
    # Update fields
    if user_data.username:
        db_user.username = user_data.username
    
    if user_data.password:
        db_user.hashed_password = get_password_hash(user_data.password)
    
    # Manually update the timestamp
    db_user.updated_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Username already exists")


def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete a user.
    
    Args:
        db: Database session
        user_id: ID of user to delete
    
    Returns:
        True if user was deleted
    
    Raises:
        ValueError: If user not found
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")
    
    db.delete(db_user)
    db.commit()
    return True


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users with pagination.
    
    Args:
        db: Database session
        skip: Number of users to skip
        limit: Maximum number of users to return
    
    Returns:
        List of User instances
    """
    return db.query(User).offset(skip).limit(limit).all()
