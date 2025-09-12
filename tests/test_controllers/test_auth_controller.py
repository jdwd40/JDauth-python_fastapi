"""
Test cases for Auth Controller using TDD methodology.

These tests define the expected behavior of the AuthController
before implementation (Red phase of TDD).
"""

import pytest
from datetime import timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.schemas.user import UserCreate
from app.schemas.auth import LoginRequest, TokenResponse
from app.models.user import User
from app.controllers.auth_controller import AuthController


class TestAuthController:
    """Test cases for AuthController business logic."""

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
        return user

    @pytest.fixture
    def auth_controller(self):
        """AuthController instance."""
        return AuthController()

    def test_register_user_success(self, auth_controller, mock_db):
        """Test successful user registration."""
        # Arrange
        user_data = UserCreate(username="newuser", password="password123")
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.username = "newuser"
        
        with patch('app.controllers.auth_controller.user_service.create_user', return_value=mock_user) as mock_create:
            # Act
            result = auth_controller.register_user(mock_db, user_data)
            
            # Assert
            mock_create.assert_called_once_with(mock_db, user_data)
            assert result == {"message": "User created successfully", "user_id": 1}

    def test_register_user_duplicate_username(self, auth_controller, mock_db):
        """Test user registration with duplicate username."""
        # Arrange
        user_data = UserCreate(username="existing_user", password="password123")
        
        with patch('app.controllers.auth_controller.user_service.create_user', side_effect=ValueError("Username already exists")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.register_user(mock_db, user_data)
            
            assert exc_info.value.status_code == 400
            assert "Username already exists" in str(exc_info.value.detail)

    def test_register_user_invalid_data(self, auth_controller, mock_db):
        """Test user registration with invalid data that passes Pydantic validation but fails business rules."""
        # Arrange - Use data that passes Pydantic but fails business rules
        user_data = UserCreate(username="validuser", password="validpass123")
        
        with patch('app.controllers.auth_controller.user_service.create_user', side_effect=ValueError("Custom business rule violation")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.register_user(mock_db, user_data)
            
            assert exc_info.value.status_code == 400
            assert "Custom business rule violation" in str(exc_info.value.detail)

    def test_login_user_success(self, auth_controller, mock_db, sample_user):
        """Test successful user login."""
        # Arrange
        credentials = LoginRequest(username="testuser", password="password123")
        expected_token = "jwt_token_here"
        
        with patch('app.controllers.auth_controller.auth_service.authenticate_user', return_value=sample_user) as mock_auth:
            with patch('app.controllers.auth_controller.auth_service.create_access_token', return_value=expected_token) as mock_token:
                # Act
                result = auth_controller.login_user(mock_db, credentials)
                
                # Assert
                mock_auth.assert_called_once_with(mock_db, "testuser", "password123")
                mock_token.assert_called_once_with(
                    data={"sub": "testuser"}, 
                    expires_delta=timedelta(minutes=30)  # Default from settings
                )
                assert isinstance(result, TokenResponse)
                assert result.access_token == expected_token
                assert result.token_type == "bearer"

    def test_login_user_invalid_credentials(self, auth_controller, mock_db):
        """Test login with invalid credentials."""
        # Arrange
        credentials = LoginRequest(username="testuser", password="wrongpassword")
        
        with patch('app.controllers.auth_controller.auth_service.authenticate_user', return_value=None):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.login_user(mock_db, credentials)
            
            assert exc_info.value.status_code == 401
            assert "Invalid credentials" in str(exc_info.value.detail)

    def test_login_user_nonexistent_user(self, auth_controller, mock_db):
        """Test login with non-existent user."""
        # Arrange
        credentials = LoginRequest(username="nonexistent", password="password123")
        
        with patch('app.controllers.auth_controller.auth_service.authenticate_user', return_value=None):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.login_user(mock_db, credentials)
            
            assert exc_info.value.status_code == 401
            assert "Invalid credentials" in str(exc_info.value.detail)

    def test_refresh_token_success(self, auth_controller, mock_db, sample_user):
        """Test successful token refresh."""
        # Arrange
        old_token = "old_jwt_token"
        new_token = "new_jwt_token"
        
        with patch('app.controllers.auth_controller.auth_service.get_current_user_from_token', return_value=sample_user) as mock_get_user:
            with patch('app.controllers.auth_controller.auth_service.create_access_token', return_value=new_token) as mock_create_token:
                # Act
                result = auth_controller.refresh_token(mock_db, old_token)
                
                # Assert
                mock_get_user.assert_called_once_with(mock_db, old_token)
                mock_create_token.assert_called_once_with(
                    data={"sub": "testuser"}, 
                    expires_delta=timedelta(minutes=30)
                )
                assert isinstance(result, TokenResponse)
                assert result.access_token == new_token
                assert result.token_type == "bearer"

    def test_refresh_token_invalid_token(self, auth_controller, mock_db):
        """Test token refresh with invalid token."""
        # Arrange
        invalid_token = "invalid_token"
        
        with patch('app.controllers.auth_controller.auth_service.get_current_user_from_token', side_effect=ValueError("Invalid token")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.refresh_token(mock_db, invalid_token)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token" in str(exc_info.value.detail)

    def test_refresh_token_expired_token(self, auth_controller, mock_db):
        """Test token refresh with expired token."""
        # Arrange
        expired_token = "expired_token"
        
        with patch('app.controllers.auth_controller.auth_service.get_current_user_from_token', side_effect=ValueError("Token has expired")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.refresh_token(mock_db, expired_token)
            
            assert exc_info.value.status_code == 401
            assert "Token has expired" in str(exc_info.value.detail)

    def test_validate_business_rules_username_length(self, auth_controller, mock_db):
        """Test business rule validation for username length at service layer."""
        # Arrange - Use valid Pydantic data but simulate service-level validation
        user_data = UserCreate(username="validuser", password="password123")
        
        with patch('app.controllers.auth_controller.user_service.create_user', side_effect=ValueError("Username validation failed")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.register_user(mock_db, user_data)
            
            assert exc_info.value.status_code == 400

    def test_validate_business_rules_password_strength(self, auth_controller, mock_db):
        """Test business rule validation for password strength at service layer."""
        # Arrange - Use valid Pydantic data but simulate service-level validation
        user_data = UserCreate(username="testuser", password="validpass123")
        
        with patch('app.controllers.auth_controller.user_service.create_user', side_effect=ValueError("Password complexity requirements not met")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.register_user(mock_db, user_data)
            
            assert exc_info.value.status_code == 400

    def test_login_rate_limiting_protection(self, auth_controller, mock_db):
        """Test that controller can handle rate limiting scenarios."""
        # Arrange
        credentials = LoginRequest(username="testuser", password="password123")
        
        # This would be handled at a higher level (middleware/routes)
        # but controller should be resilient
        with patch('app.controllers.auth_controller.auth_service.authenticate_user', side_effect=Exception("Database connection timeout")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.login_user(mock_db, credentials)
            
            assert exc_info.value.status_code == 500
            assert "Internal server error" in str(exc_info.value.detail)

    def test_register_handles_database_errors(self, auth_controller, mock_db):
        """Test registration handles database errors gracefully."""
        # Arrange
        user_data = UserCreate(username="testuser", password="password123")
        
        with patch('app.controllers.auth_controller.user_service.create_user', side_effect=Exception("Database connection failed")):
            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                auth_controller.register_user(mock_db, user_data)
            
            assert exc_info.value.status_code == 500
            assert "Internal server error" in str(exc_info.value.detail)
