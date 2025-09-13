"""
User service for handling user-related business logic and data operations.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserRole
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
    
    # Create new user with hashed password and default role
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        hashed_password=hashed_password,
        role=user_data.role.value if user_data.role else UserRole.USER.value,
        is_active=True
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
    
    if user_data.role is not None:
        db_user.role = user_data.role.value
    
    if user_data.is_active is not None:
        db_user.is_active = user_data.is_active
    
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


# Role Management Functions

def create_user_with_role(db: Session, user_data: UserCreate, role: str) -> User:
    """
    Create a new user with a specific role.
    
    Args:
        db: Database session
        user_data: User creation data
        role: Role to assign to the user
    
    Returns:
        Created User instance
    
    Raises:
        ValueError: If username already exists, invalid data, or invalid role
    """
    # Validate role
    if role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        raise ValueError(f"Invalid role: {role}")
    
    # Temporarily override the role in user_data
    user_data.role = UserRole(role)
    
    return create_user(db, user_data)


def assign_user_role(db: Session, user_id: int, role: str, requesting_user_id: Optional[int] = None) -> User:
    """
    Assign a role to a user.
    
    Args:
        db: Database session
        user_id: ID of user to update
        role: Role to assign
        requesting_user_id: ID of user making the request (for safety checks)
    
    Returns:
        Updated User instance
    
    Raises:
        ValueError: If user not found, invalid role, or safety check fails
    """
    # Validate role
    if role not in [UserRole.ADMIN.value, UserRole.USER.value]:
        raise ValueError(f"Invalid role: {role}")
    
    # Get existing user
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")
    
    # Safety check: prevent admin from modifying their own role
    if requesting_user_id and requesting_user_id == user_id:
        raise ValueError("Cannot modify your own role")
    
    # Update role
    db_user.role = role
    db_user.updated_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update user role: {str(e)}")


def set_user_status(db: Session, user_id: int, is_active: bool, requesting_user_id: Optional[int] = None) -> User:
    """
    Set a user's active status.
    
    Args:
        db: Database session
        user_id: ID of user to update
        is_active: Active status to set
        requesting_user_id: ID of user making the request (for safety checks)
    
    Returns:
        Updated User instance
    
    Raises:
        ValueError: If user not found or safety check fails
    """
    # Get existing user
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")
    
    # Safety check: prevent admin from deactivating themselves
    if requesting_user_id and requesting_user_id == user_id and not is_active:
        raise ValueError("Cannot modify your own status")
    
    # Update status
    db_user.is_active = is_active
    db_user.updated_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to update user status: {str(e)}")


def get_users_by_role(db: Session, role: str, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get users filtered by role.
    
    Args:
        db: Database session
        role: Role to filter by
        skip: Number of users to skip
        limit: Maximum number of users to return
    
    Returns:
        List of User instances with the specified role
    """
    return db.query(User).filter(User.role == role).offset(skip).limit(limit).all()


def get_users_by_status(db: Session, is_active: bool, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get users filtered by active status.
    
    Args:
        db: Database session
        is_active: Active status to filter by
        skip: Number of users to skip
        limit: Maximum number of users to return
    
    Returns:
        List of User instances with the specified status
    """
    return db.query(User).filter(User.is_active == is_active).offset(skip).limit(limit).all()


def count_users_by_role(db: Session, role: str) -> int:
    """
    Count users by role.
    
    Args:
        db: Database session
        role: Role to count
    
    Returns:
        Number of users with the specified role
    """
    return db.query(User).filter(User.role == role).count()


def count_users_by_status(db: Session, is_active: bool) -> int:
    """
    Count users by active status.
    
    Args:
        db: Database session
        is_active: Active status to count
    
    Returns:
        Number of users with the specified status
    """
    return db.query(User).filter(User.is_active == is_active).count()
