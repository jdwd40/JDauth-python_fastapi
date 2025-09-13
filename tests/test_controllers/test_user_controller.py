"""
Test cases for User Controller using TDD methodology.

These tests define the expected behavior of the UserController
before implementation (Red phase of TDD).
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.schemas.user import UserUpdate, UserResponse
from app.models.user import User
from app.controllers.user_controller import UserController


class TestUserController:
    """Test cases for UserController business logic."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.hashed_password = "hashed_password"
        user.role = "user"
        user.is_active = True
        user.created_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        return user

    @pytest.fixture
    def admin_user(self):
        """Sample admin user for testing."""
        user = Mock(spec=User)
        user.id = 2
        user.username = "admin"
        user.hashed_password = "admin_password"
        user.role = "admin"
        user.is_active = True
        user.created_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        return user

    @pytest.fixture
    def user_controller(self):
        """UserController instance."""
        return UserController()

    def test_get_current_user_profile_success(self, user_controller, sample_user):
        """Test getting current user profile."""
        # Act
        result = user_controller.get_current_user_profile(sample_user)
        
        # Assert
        assert isinstance(result, UserResponse)
        assert result.id == sample_user.id
        assert result.username == sample_user.username

    def test_get_current_user_profile_none_user(self, user_controller):
        """Test getting profile with None user."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            user_controller.get_current_user_profile(None)
        
        assert exc_info.value.status_code == 401
        assert "User not authenticated" in str(exc_info.value.detail)

    def test_update_user_profile_success(self, user_controller, mock_db, sample_user):
        """Test successful user profile update."""
        # Arrange
        update_data = UserUpdate(username="updated_user", password="new_password123")
        updated_user = Mock(spec=User)
        updated_user.id = 1
        updated_user.username = "updated_user"
        updated_user.role = "user"
        updated_user.is_active = True
        updated_user.created_at = datetime.now(timezone.utc)
        updated_user.updated_at = datetime.now(timezone.utc)
        
        with patch('app.controllers.user_controller.user_service.update_user', return_value=updated_user) as mock_update:
            # Act
            result = user_controller.update_user_profile(mock_db, sample_user, update_data)
            
            # Assert
            mock_update.assert_called_once_with(mock_db, sample_user.id, update_data)
            assert isinstance(result, UserResponse)
            assert result.id == updated_user.id
            assert result.username == updated_user.username

    def test_update_user_profile_duplicate_username(self, user_controller, mock_db, sample_user):
        """Test profile update with duplicate username."""
        # Arrange
        update_data = UserUpdate(username="existing_user")
        
        with patch('app.controllers.user_controller.user_service.update_user', side_effect=ValueError("Username already exists")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                user_controller.update_user_profile(mock_db, sample_user, update_data)
            
            assert exc_info.value.status_code == 400
            assert "Username already exists" in str(exc_info.value.detail)

    def test_update_user_profile_invalid_data(self, user_controller, mock_db, sample_user):
        """Test profile update with invalid data that passes Pydantic but fails business rules."""
        # Arrange - Use data that passes Pydantic but fails business rules
        update_data = UserUpdate(username="validname", password="validpass123")
        
        with patch('app.controllers.user_controller.user_service.update_user', side_effect=ValueError("Custom business rule violation")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                user_controller.update_user_profile(mock_db, sample_user, update_data)
            
            assert exc_info.value.status_code == 400
            assert "Custom business rule violation" in str(exc_info.value.detail)

    def test_update_user_profile_none_user(self, user_controller, mock_db):
        """Test profile update with None user."""
        # Arrange
        update_data = UserUpdate(username="new_name")
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            user_controller.update_user_profile(mock_db, None, update_data)
        
        assert exc_info.value.status_code == 401
        assert "User not authenticated" in str(exc_info.value.detail)

    def test_get_user_list_admin_success(self, user_controller, mock_db, admin_user):
        """Test getting user list as admin."""
        # Arrange
        now = datetime.now(timezone.utc)
        mock_users = []
        for i in range(1, 4):
            user = Mock(spec=User)
            user.id = i
            user.username = f"user{i}"
            user.role = "user"
            user.is_active = True
            user.created_at = now
            mock_users.append(user)
        
        with patch('app.controllers.user_controller.user_service.get_users', return_value=mock_users) as mock_get_users:
            # Act
            result = user_controller.get_user_list(mock_db, admin_user, skip=0, limit=10)
            
            # Assert
            mock_get_users.assert_called_once_with(mock_db, skip=0, limit=10)
            assert isinstance(result, list)
            assert len(result) == 3
            for user_response in result:
                assert isinstance(user_response, UserResponse)

    def test_get_user_list_non_admin_forbidden(self, user_controller, mock_db, sample_user):
        """Test getting user list as non-admin user (should be forbidden)."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            user_controller.get_user_list(mock_db, sample_user, skip=0, limit=10)
        
        assert exc_info.value.status_code == 403
        assert "Admin access required" in str(exc_info.value.detail)

    def test_get_user_list_none_user(self, user_controller, mock_db):
        """Test getting user list with None user."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            user_controller.get_user_list(mock_db, None, skip=0, limit=10)
        
        assert exc_info.value.status_code == 401
        assert "User not authenticated" in str(exc_info.value.detail)

    def test_get_user_list_pagination_validation(self, user_controller, mock_db, admin_user):
        """Test user list pagination parameter validation."""
        # Test negative skip
        with pytest.raises(HTTPException) as exc_info:
            user_controller.get_user_list(mock_db, admin_user, skip=-1, limit=10)
        
        assert exc_info.value.status_code == 400
        assert "Skip cannot be negative" in str(exc_info.value.detail)

        # Test invalid limit
        with pytest.raises(HTTPException) as exc_info:
            user_controller.get_user_list(mock_db, admin_user, skip=0, limit=0)
        
        assert exc_info.value.status_code == 400
        assert "Limit must be positive" in str(exc_info.value.detail)

        # Test limit too high
        with pytest.raises(HTTPException) as exc_info:
            user_controller.get_user_list(mock_db, admin_user, skip=0, limit=1000)
        
        assert exc_info.value.status_code == 400
        assert "Limit cannot exceed 100" in str(exc_info.value.detail)

    def test_update_user_profile_handles_database_errors(self, user_controller, mock_db, sample_user):
        """Test profile update handles database errors gracefully."""
        # Arrange
        update_data = UserUpdate(username="new_user")
        
        with patch('app.controllers.user_controller.user_service.update_user', side_effect=Exception("Database connection failed")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                user_controller.update_user_profile(mock_db, sample_user, update_data)
            
            assert exc_info.value.status_code == 500
            assert "Internal server error" in str(exc_info.value.detail)

    def test_get_user_list_handles_database_errors(self, user_controller, mock_db, admin_user):
        """Test user list handles database errors gracefully."""
        with patch('app.controllers.user_controller.user_service.get_users', side_effect=Exception("Database connection failed")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                user_controller.get_user_list(mock_db, admin_user, skip=0, limit=10)
            
            assert exc_info.value.status_code == 500
            assert "Internal server error" in str(exc_info.value.detail)

    def test_business_rule_username_uniqueness(self, user_controller, mock_db, sample_user):
        """Test business rule enforcement for username uniqueness."""
        # Arrange
        update_data = UserUpdate(username="admin")  # Assuming this exists
        
        with patch('app.controllers.user_controller.user_service.update_user', side_effect=ValueError("Username already exists")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                user_controller.update_user_profile(mock_db, sample_user, update_data)
            
            assert exc_info.value.status_code == 400

    def test_business_rule_password_complexity(self, user_controller, mock_db, sample_user):
        """Test business rule enforcement for password complexity at service layer."""
        # Arrange - Use valid Pydantic data but simulate service-level validation
        update_data = UserUpdate(password="validpass123")
        
        with patch('app.controllers.user_controller.user_service.update_user', side_effect=ValueError("Password complexity requirements not met")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                user_controller.update_user_profile(mock_db, sample_user, update_data)
            
            assert exc_info.value.status_code == 400
