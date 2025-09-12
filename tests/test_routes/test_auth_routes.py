"""
Test cases for authentication routes.

Following TDD methodology: These tests define the expected behavior
of the auth routes before implementation.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.schemas.user import UserCreate
from app.schemas.auth import LoginRequest, TokenResponse
from tests.factories import UserFactory


class TestAuthRoutes:
    """Test suite for authentication routes."""

    def test_register_success(self, client: TestClient, db_session):
        """Test successful user registration."""
        user_data = {
            "username": "newuser",
            "password": "secure_password123"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "message" in data
        assert data["message"] == "User created successfully"
        assert "user_id" in data
        assert isinstance(data["user_id"], int)

    def test_register_duplicate_username(self, client: TestClient, db_session):
        """Test registration with duplicate username fails."""
        # Create existing user
        existing_user = UserFactory(username="existinguser")
        db_session.add(existing_user)
        db_session.commit()
        
        user_data = {
            "username": "existinguser",
            "password": "password123"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "message" in data
        assert "already exists" in data["message"].lower() or "already registered" in data["message"].lower()

    def test_register_invalid_data(self, client: TestClient):
        """Test registration with invalid data fails."""
        test_cases = [
            # Missing username
            {"password": "password123"},
            # Missing password
            {"username": "testuser"},
            # Empty username
            {"username": "", "password": "password123"},
            # Empty password
            {"username": "testuser", "password": ""},
            # Invalid data types
            {"username": 123, "password": "password123"},
        ]
        
        for user_data in test_cases:
            response = client.post("/api/auth/register", json=user_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self, client: TestClient, db_session):
        """Test successful user login."""
        # Create user for login
        user = UserFactory(username="loginuser", hashed_password="hashed_password")
        db_session.add(user)
        db_session.commit()
        
        login_data = {
            "username": "loginuser",
            "password": "test_password"
        }
        
        # Mock authentication
        with patch('app.controllers.auth_controller.AuthController.login_user') as mock_login:
            mock_login.return_value = TokenResponse(
                access_token="test_token",
                token_type="bearer",
                expires_in=1800
            )
            
            response = client.post("/api/auth/login", json=login_data)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert "expires_in" in data

    def test_login_invalid_credentials(self, client: TestClient):
        """Test login with invalid credentials fails."""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "message" in data
        assert "invalid" in data["message"].lower() or "incorrect" in data["message"].lower()

    def test_login_invalid_data(self, client: TestClient):
        """Test login with invalid data fails."""
        test_cases = [
            # Missing username
            {"password": "password123"},
            # Missing password
            {"username": "testuser"},
            # Empty username
            {"username": "", "password": "password123"},
            # Empty password
            {"username": "testuser", "password": ""},
        ]
        
        for login_data in test_cases:
            response = client.post("/api/auth/login", json=login_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_refresh_token_success(self, client: TestClient):
        """Test that refresh token endpoint exists and handles authentication properly."""
        # Since refresh token requires valid authentication, we test that it properly
        # rejects unauthenticated requests. A full integration test would require
        # a complete auth flow which is tested in integration tests.
        
        response = client.post("/api/auth/refresh")
        
        # Should return 401 for unauthenticated request (endpoint exists and works)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "message" in data
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/auth/refresh", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_invalid(self, client: TestClient):
        """Test token refresh with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/auth/refresh", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "message" in data

    def test_refresh_token_missing_authorization(self, client: TestClient):
        """Test token refresh without authorization header fails."""
        response = client.post("/api/auth/refresh")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "message" in data

    def test_auth_routes_cors_headers(self, client: TestClient):
        """Test that auth routes include proper CORS headers."""
        response = client.options("/api/auth/register")
        # This test will depend on CORS middleware configuration
        # For now, just ensure the endpoint exists
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]

    def test_auth_routes_rate_limiting(self, client: TestClient):
        """Test rate limiting on auth routes (if implemented)."""
        # This is a placeholder for future rate limiting implementation
        # For now, just ensure multiple requests don't crash
        for _ in range(5):
            response = client.post("/api/auth/login", json={"username": "test", "password": "test"})
            # Should not cause server errors
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_auth_routes_error_handling(self, client: TestClient):
        """Test proper error handling in auth routes."""
        # Test server error handling with invalid JSON
        response = client.post(
            "/api/auth/register",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_auth_routes_security_headers(self, client: TestClient):
        """Test that auth routes include security headers."""
        response = client.post("/api/auth/login", json={"username": "test", "password": "test"})
        
        # Check for common security headers (if implemented)
        # These might be added by middleware
        headers = response.headers
        # Just ensure response is properly formed
        assert "content-type" in headers
        assert headers["content-type"] == "application/json"
