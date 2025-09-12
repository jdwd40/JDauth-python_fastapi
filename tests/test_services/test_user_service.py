"""
Test suite for user service using Test-Driven Development (TDD).
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.services.user_service import (
    create_user,
    get_user_by_username,
    get_user_by_id,
    update_user,
    delete_user,
    get_users
)
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from tests.factories import (
    UserCreateFactory,
    UserUpdateFactory,
    create_user_in_db,
    create_multiple_users_in_db
)


class TestCreateUser:
    """Test cases for user creation."""
    
    @pytest.mark.unit
    def test_create_user_success(self, db_session: Session):
        """Test successful user creation with valid data."""
        # Arrange
        user_data = UserCreateFactory()
        
        # Act
        created_user = create_user(db_session, user_data)
        
        # Assert
        assert created_user is not None
        assert created_user.username == user_data.username
        assert created_user.id is not None
        assert created_user.hashed_password != user_data.password  # Should be hashed
        assert created_user.created_at is not None
        assert created_user.updated_at is not None
    
    @pytest.mark.unit
    def test_create_user_duplicate_username(self, db_session: Session):
        """Test user creation fails with duplicate username."""
        # Arrange
        username = "duplicate_user"
        existing_user = create_user_in_db(db_session, username=username)
        user_data = UserCreateFactory(username=username)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Username already exists"):
            create_user(db_session, user_data)
    
    @pytest.mark.unit
    def test_create_user_invalid_data(self, db_session: Session):
        """Test user creation with invalid data."""
        # Arrange - Test service-level validation for edge cases
        # Since Pydantic validation happens first, we test empty strings after creation
        user_data = UserCreateFactory(username="   ", password="123456")  # Whitespace username
        
        # Act & Assert
        with pytest.raises(ValueError):
            create_user(db_session, user_data)


class TestGetUserByUsername:
    """Test cases for getting user by username."""
    
    @pytest.mark.unit
    def test_get_user_by_username_exists(self, db_session: Session):
        """Test retrieving an existing user by username."""
        # Arrange
        username = "existing_user"
        existing_user = create_user_in_db(db_session, username=username)
        
        # Act
        found_user = get_user_by_username(db_session, username)
        
        # Assert
        assert found_user is not None
        assert found_user.id == existing_user.id
        assert found_user.username == username
    
    @pytest.mark.unit
    def test_get_user_by_username_not_found(self, db_session: Session):
        """Test retrieving a non-existent user by username."""
        # Arrange
        username = "nonexistent_user"
        
        # Act
        found_user = get_user_by_username(db_session, username)
        
        # Assert
        assert found_user is None
    
    @pytest.mark.unit
    def test_get_user_by_username_case_sensitive(self, db_session: Session):
        """Test that username search is case sensitive."""
        # Arrange
        username = "CaseSensitive"
        create_user_in_db(db_session, username=username)
        
        # Act
        found_user = get_user_by_username(db_session, "casesensitive")
        
        # Assert
        assert found_user is None


class TestGetUserById:
    """Test cases for getting user by ID."""
    
    @pytest.mark.unit
    def test_get_user_by_id_exists(self, db_session: Session):
        """Test retrieving an existing user by ID."""
        # Arrange
        existing_user = create_user_in_db(db_session, username="test_user")
        
        # Act
        found_user = get_user_by_id(db_session, existing_user.id)
        
        # Assert
        assert found_user is not None
        assert found_user.id == existing_user.id
        assert found_user.username == existing_user.username
    
    @pytest.mark.unit
    def test_get_user_by_id_not_found(self, db_session: Session):
        """Test retrieving a non-existent user by ID."""
        # Arrange
        non_existent_id = 999999
        
        # Act
        found_user = get_user_by_id(db_session, non_existent_id)
        
        # Assert
        assert found_user is None
    
    @pytest.mark.unit
    def test_get_user_by_id_invalid_id(self, db_session: Session):
        """Test retrieving user with invalid ID."""
        # Act & Assert
        with pytest.raises(ValueError):
            get_user_by_id(db_session, -1)


class TestUpdateUser:
    """Test cases for updating user."""
    
    @pytest.mark.unit
    def test_update_user_success(self, db_session: Session):
        """Test successful user update."""
        # Arrange
        existing_user = create_user_in_db(db_session, username="old_username")
        original_updated_at = existing_user.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        update_data = UserUpdateFactory(username="new_username")
        
        # Act
        updated_user = update_user(db_session, existing_user.id, update_data)
        
        # Assert
        assert updated_user is not None
        assert updated_user.id == existing_user.id
        assert updated_user.username == "new_username"
        assert updated_user.updated_at >= original_updated_at
    
    @pytest.mark.unit
    def test_update_user_not_found(self, db_session: Session):
        """Test updating a non-existent user."""
        # Arrange
        non_existent_id = 999999
        update_data = UserUpdateFactory()
        
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            update_user(db_session, non_existent_id, update_data)
    
    @pytest.mark.unit
    def test_update_user_duplicate_username(self, db_session: Session):
        """Test updating user with existing username."""
        # Arrange
        user1 = create_user_in_db(db_session, username="user1")
        user2 = create_user_in_db(db_session, username="user2")
        update_data = UserUpdate(username="user1")  # Try to use user1's username
        
        # Act & Assert
        with pytest.raises(ValueError, match="Username already exists"):
            update_user(db_session, user2.id, update_data)
    
    @pytest.mark.unit
    def test_update_user_partial_update(self, db_session: Session):
        """Test partial user update (only username or password)."""
        # Arrange
        existing_user = create_user_in_db(db_session, username="old_user")
        old_password_hash = existing_user.hashed_password
        update_data = UserUpdate(username="new_user")  # Only update username
        
        # Act
        updated_user = update_user(db_session, existing_user.id, update_data)
        
        # Assert
        assert updated_user.username == "new_user"
        assert updated_user.hashed_password == old_password_hash  # Password unchanged


class TestDeleteUser:
    """Test cases for deleting user."""
    
    @pytest.mark.unit
    def test_delete_user_success(self, db_session: Session):
        """Test successful user deletion."""
        # Arrange
        existing_user = create_user_in_db(db_session, username="to_delete")
        user_id = existing_user.id
        
        # Act
        result = delete_user(db_session, user_id)
        
        # Assert
        assert result is True
        deleted_user = get_user_by_id(db_session, user_id)
        assert deleted_user is None
    
    @pytest.mark.unit
    def test_delete_user_not_found(self, db_session: Session):
        """Test deleting a non-existent user."""
        # Arrange
        non_existent_id = 999999
        
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            delete_user(db_session, non_existent_id)


class TestGetUsers:
    """Test cases for listing users with pagination."""
    
    @pytest.mark.unit
    def test_get_users_pagination(self, db_session: Session):
        """Test getting users with pagination."""
        # Arrange
        users = create_multiple_users_in_db(db_session, count=10)
        
        # Act
        first_page = get_users(db_session, skip=0, limit=5)
        second_page = get_users(db_session, skip=5, limit=5)
        
        # Assert
        assert len(first_page) == 5
        assert len(second_page) == 5
        
        # Ensure no overlap
        first_page_ids = {user.id for user in first_page}
        second_page_ids = {user.id for user in second_page}
        assert first_page_ids.isdisjoint(second_page_ids)
    
    @pytest.mark.unit
    def test_get_users_empty_database(self, db_session: Session):
        """Test getting users from empty database."""
        # Ensure database is clean for this test
        db_session.query(User).delete()
        db_session.commit()
        
        # Act
        users = get_users(db_session, skip=0, limit=10)
        
        # Assert
        assert users == []
    
    @pytest.mark.unit
    def test_get_users_default_parameters(self, db_session: Session):
        """Test getting users with default pagination parameters."""
        # Ensure clean state
        db_session.query(User).delete()
        db_session.commit()
        
        # Arrange
        create_multiple_users_in_db(db_session, count=3)
        
        # Act
        users = get_users(db_session)
        
        # Assert
        assert len(users) == 3
    
    @pytest.mark.unit
    def test_get_users_limit_exceeds_available(self, db_session: Session):
        """Test getting users when limit exceeds available users."""
        # Ensure clean state
        db_session.query(User).delete()
        db_session.commit()
        
        # Arrange
        create_multiple_users_in_db(db_session, count=3)
        
        # Act
        users = get_users(db_session, skip=0, limit=10)
        
        # Assert
        assert len(users) == 3
