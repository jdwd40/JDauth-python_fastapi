"""
Test data factories for generating consistent test data.
"""

import factory
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.auth import LoginRequest


class UserFactory(factory.Factory):
    """Factory for creating User model instances."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"testuser{n}")
    hashed_password = factory.LazyAttribute(
        lambda obj: "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p02TrN5eTfGir2D6GlgL2m3u"  # "secret"
    )
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class UserCreateFactory(factory.Factory):
    """Factory for creating UserCreate schema instances."""
    
    class Meta:
        model = UserCreate
    
    username = factory.Sequence(lambda n: f"newuser{n}")
    password = "testpassword123"


class UserUpdateFactory(factory.Factory):
    """Factory for creating UserUpdate schema instances."""
    
    class Meta:
        model = UserUpdate
    
    username = factory.Sequence(lambda n: f"updateduser{n}")
    password = "updatedpassword123"


class LoginRequestFactory(factory.Factory):
    """Factory for creating LoginRequest schema instances."""
    
    class Meta:
        model = LoginRequest
    
    username = factory.Sequence(lambda n: f"loginuser{n}")
    password = "loginpassword123"


def create_user_in_db(db: Session, **kwargs) -> User:
    """
    Helper function to create a user directly in the database.
    
    Args:
        db: Database session
        **kwargs: Additional user attributes
    
    Returns:
        Created User instance
    """
    user_data = {
        "username": kwargs.get("username", "dbuser"),
        "hashed_password": kwargs.get(
            "hashed_password", 
            "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p02TrN5eTfGir2D6GlgL2m3u"  # "secret"
        )
    }
    user_data.update(kwargs)
    
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_multiple_users_in_db(db: Session, count: int = 5) -> list[User]:
    """
    Helper function to create multiple users in the database.
    
    Args:
        db: Database session
        count: Number of users to create
    
    Returns:
        List of created User instances
    """
    users = []
    for i in range(count):
        user = create_user_in_db(
            db,
            username=f"bulkuser{i}",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p02TrN5eTfGir2D6GlgL2m3u"
        )
        users.append(user)
    return users
