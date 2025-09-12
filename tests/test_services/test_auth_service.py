"""
Test suite for authentication service using Test-Driven Development (TDD).
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from jose import jwt

from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    verify_token,
    get_current_user_from_token
)
from app.schemas.auth import LoginRequest
from app.models.user import User
from tests.factories import (
    LoginRequestFactory,
    create_user_in_db
)


class TestAuthenticateUser:
    """Test cases for user authentication."""
    
    @pytest.mark.unit
    def test_authenticate_user_success(self, db_session: Session):
        """Test successful user authentication with valid credentials."""
        # Arrange
        password = "testpassword123"
        user = create_user_in_db(
            db_session, 
            username="testuser",
            # This is the bcrypt hash for "testpassword123"
            hashed_password="$2b$12$MMjIVR2KdAh2e5gjSIdpSuhqDfLriVoebm94YbkQR/hIVjbChTIFy"
        )
        
        # Act
        authenticated_user = authenticate_user(db_session, "testuser", password)
        
        # Assert
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.username == "testuser"
    
    @pytest.mark.unit
    def test_authenticate_user_invalid_password(self, db_session: Session):
        """Test authentication with invalid password."""
        # Arrange
        user = create_user_in_db(
            db_session,
            username="testuser",
            hashed_password="$2b$12$MMjIVR2KdAh2e5gjSIdpSuhqDfLriVoebm94YbkQR/hIVjbChTIFy"
        )
        
        # Act
        authenticated_user = authenticate_user(db_session, "testuser", "wrongpassword")
        
        # Assert
        assert authenticated_user is None
    
    @pytest.mark.unit
    def test_authenticate_user_nonexistent(self, db_session: Session):
        """Test authentication with non-existent user."""
        # Act
        authenticated_user = authenticate_user(db_session, "nonexistent", "password")
        
        # Assert
        assert authenticated_user is None
    
    @pytest.mark.unit
    def test_authenticate_user_empty_credentials(self, db_session: Session):
        """Test authentication with empty credentials."""
        # Act & Assert
        assert authenticate_user(db_session, "", "password") is None
        assert authenticate_user(db_session, "user", "") is None
        assert authenticate_user(db_session, "", "") is None


class TestCreateAccessToken:
    """Test cases for JWT token creation."""
    
    @pytest.mark.unit
    def test_create_access_token(self):
        """Test JWT token creation with valid data."""
        # Arrange
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        
        # Act
        token = create_access_token(data, expires_delta)
        
        # Assert
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token structure (should have 3 parts separated by dots)
        token_parts = token.split('.')
        assert len(token_parts) == 3
    
    @pytest.mark.unit
    def test_create_access_token_default_expiration(self):
        """Test JWT token creation with default expiration."""
        # Arrange
        data = {"sub": "testuser"}
        
        # Act
        token = create_access_token(data)
        
        # Assert
        assert token is not None
        assert isinstance(token, str)
    
    @pytest.mark.unit
    def test_create_access_token_custom_data(self):
        """Test JWT token creation with custom data."""
        # Arrange
        data = {
            "sub": "testuser",
            "role": "admin",
            "permissions": ["read", "write"]
        }
        
        # Act
        token = create_access_token(data)
        
        # Assert
        assert token is not None
        assert isinstance(token, str)
    
    @pytest.mark.unit
    def test_create_access_token_empty_data(self):
        """Test JWT token creation with empty data."""
        # Act & Assert
        with pytest.raises(ValueError):
            create_access_token({})


class TestVerifyToken:
    """Test cases for JWT token verification."""
    
    @pytest.mark.unit
    def test_verify_token_valid(self):
        """Test verification of valid JWT token."""
        # Arrange
        data = {"sub": "testuser"}
        token = create_access_token(data, timedelta(minutes=30))
        
        # Act
        payload = verify_token(token)
        
        # Assert
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    @pytest.mark.unit
    def test_verify_token_expired(self):
        """Test verification of expired JWT token."""
        # Arrange
        data = {"sub": "testuser"}
        # Create token that expires immediately
        expired_token = create_access_token(data, timedelta(seconds=-1))
        
        # Act & Assert
        with pytest.raises(ValueError, match="Token has expired"):
            verify_token(expired_token)
    
    @pytest.mark.unit
    def test_verify_token_invalid(self):
        """Test verification of invalid JWT token."""
        # Arrange
        invalid_token = "invalid.token.here"
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid token"):
            verify_token(invalid_token)
    
    @pytest.mark.unit
    def test_verify_token_malformed(self):
        """Test verification of malformed JWT token."""
        # Arrange
        malformed_tokens = [
            "not.a.token",
            "missing_parts",
            "",
            None
        ]
        
        # Act & Assert
        for token in malformed_tokens:
            with pytest.raises(ValueError, match="Invalid token"):
                verify_token(token)
    
    @pytest.mark.unit
    def test_verify_token_tampered(self):
        """Test verification of tampered JWT token."""
        # Arrange
        data = {"sub": "testuser"}
        token = create_access_token(data)
        # Tamper with the token by changing a character
        tampered_token = token[:-1] + 'X'
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid token"):
            verify_token(tampered_token)


class TestGetCurrentUserFromToken:
    """Test cases for extracting user from JWT token."""
    
    @pytest.mark.unit
    def test_get_current_user_from_token(self, db_session: Session):
        """Test extracting user from valid JWT token."""
        # Arrange
        user = create_user_in_db(db_session, username="testuser")
        data = {"sub": user.username}
        token = create_access_token(data)
        
        # Act
        current_user = get_current_user_from_token(db_session, token)
        
        # Assert
        assert current_user is not None
        assert current_user.id == user.id
        assert current_user.username == user.username
    
    @pytest.mark.unit
    def test_get_current_user_from_token_user_not_found(self, db_session: Session):
        """Test extracting user from token when user doesn't exist in database."""
        # Arrange
        data = {"sub": "nonexistent_user"}
        token = create_access_token(data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            get_current_user_from_token(db_session, token)
    
    @pytest.mark.unit
    def test_get_current_user_from_token_invalid_token(self, db_session: Session):
        """Test extracting user from invalid JWT token."""
        # Arrange
        invalid_token = "invalid.token.here"
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid token"):
            get_current_user_from_token(db_session, invalid_token)
    
    @pytest.mark.unit
    def test_get_current_user_from_token_expired(self, db_session: Session):
        """Test extracting user from expired JWT token."""
        # Arrange
        user = create_user_in_db(db_session, username="testuser")
        data = {"sub": user.username}
        expired_token = create_access_token(data, timedelta(seconds=-1))
        
        # Act & Assert
        with pytest.raises(ValueError, match="Token has expired"):
            get_current_user_from_token(db_session, expired_token)
    
    @pytest.mark.unit
    def test_get_current_user_from_token_no_subject(self, db_session: Session):
        """Test extracting user from token without subject."""
        # Arrange
        data = {"role": "admin"}  # No 'sub' field
        token = create_access_token(data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid token payload"):
            get_current_user_from_token(db_session, token)


class TestPasswordVerification:
    """Test cases for password verification utilities."""
    
    @pytest.mark.unit
    def test_password_hashing_and_verification(self):
        """Test password hashing and verification process."""
        # This will be tested indirectly through authenticate_user tests
        # but we can add specific tests for password utilities if needed
        pass


class TestIntegrationAuthFlow:
    """Integration tests for complete authentication flow."""
    
    @pytest.mark.integration
    def test_complete_auth_flow(self, db_session: Session):
        """Test complete authentication flow from user creation to token verification."""
        # Arrange
        password = "testpassword123"
        user = create_user_in_db(
            db_session,
            username="integrationuser",
            hashed_password="$2b$12$MMjIVR2KdAh2e5gjSIdpSuhqDfLriVoebm94YbkQR/hIVjbChTIFy"
        )
        
        # Act 1: Authenticate user
        authenticated_user = authenticate_user(db_session, user.username, password)
        assert authenticated_user is not None
        
        # Act 2: Create token
        token_data = {"sub": authenticated_user.username}
        token = create_access_token(token_data, timedelta(minutes=30))
        assert token is not None
        
        # Act 3: Verify token
        payload = verify_token(token)
        assert payload["sub"] == user.username
        
        # Act 4: Get user from token
        token_user = get_current_user_from_token(db_session, token)
        assert token_user.id == user.id
        assert token_user.username == user.username
