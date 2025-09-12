"""
Test cases for user routes.

Following TDD methodology: These tests define the expected behavior
of the user routes before implementation.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.schemas.user import UserResponse, UserUpdate
from tests.factories import UserFactory


class TestUserRoutes:
    """Test suite for user routes."""

    def test_get_profile_success(self, authenticated_client):
        """Test successful retrieval of user profile."""
        client, user = authenticated_client
        
        response = client.get("/user/profile")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert data["username"] == user.username
        assert "created_at" in data

    def test_get_profile_unauthorized(self, client: TestClient):
        """Test profile retrieval without authentication fails."""
        response = client.get("/user/profile")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data

    def test_get_profile_invalid_token(self, client: TestClient):
        """Test profile retrieval with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/user/profile", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data

    def test_update_profile_success(self, authenticated_client):
        """Test successful profile update."""
        client, user = authenticated_client
        
        update_data = {
            "username": "newusername"
        }
        
        response = client.put("/user/profile", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "username" in data

    def test_update_profile_unauthorized(self, client: TestClient):
        """Test profile update without authentication fails."""
        update_data = {"username": "newusername"}
        
        response = client.put("/user/profile", json=update_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data

    def test_update_profile_invalid_data(self, authenticated_client):
        """Test profile update with invalid data fails."""
        client, user = authenticated_client
        
        test_cases = [
            # Empty username
            {"username": ""},
            # Username too short (if validation exists)
            {"username": "a"},
            # Invalid data type
            {"username": 123},
        ]
        
        for update_data in test_cases:
            response = client.put("/user/profile", json=update_data)
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_protected_endpoint_success(self, authenticated_client):
        """Test successful access to protected endpoint."""
        client, user = authenticated_client
        
        response = client.get("/user/protected")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert user.username in data["message"]

    def test_protected_endpoint_unauthorized(self, client: TestClient):
        """Test protected endpoint without authentication fails."""
        response = client.get("/user/protected")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data

    def test_get_users_list_success_admin(self, admin_client):
        """Test successful retrieval of users list by admin."""
        client, admin_user = admin_client
        
        response = client.get("/users")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # At least the admin user should be in the list
        assert len(data) >= 1
        for user_data in data:
            assert "id" in user_data
            assert "username" in user_data
            assert "created_at" in user_data

    def test_get_users_list_with_pagination(self, admin_client):
        """Test users list with pagination parameters."""
        client, admin_user = admin_client
        
        response = client.get("/users?skip=0&limit=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return at most 5 users due to limit
        assert len(data) <= 5

    def test_get_users_list_forbidden_non_admin(self, authenticated_client):
        """Test users list access denied for non-admin users."""
        client, regular_user = authenticated_client
        
        response = client.get("/users")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "detail" in data
        assert "admin" in data["detail"].lower()

    def test_get_users_list_unauthorized(self, client: TestClient):
        """Test users list without authentication fails."""
        response = client.get("/users")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data

    def test_get_users_list_invalid_pagination(self, admin_client):
        """Test users list with invalid pagination parameters."""
        client, admin_user = admin_client
        
        # Test invalid pagination parameters
        test_cases = [
            "?skip=-1",  # Negative skip
            "?limit=0",  # Zero limit
            "?limit=101",  # Limit too high
            "?skip=abc",  # Non-numeric skip
            "?limit=xyz",  # Non-numeric limit
        ]
        
        for params in test_cases:
            response = client.get(f"/users{params}")
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_user_routes_error_handling(self, client: TestClient):
        """Test proper error handling in user routes."""
        # Test with malformed requests
        headers = {"Authorization": "Bearer valid_token"}
        
        # Invalid JSON for profile update
        response = client.put(
            "/user/profile",
            data="invalid json",
            headers={**headers, "Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_user_routes_response_format(self, authenticated_client):
        """Test that user routes return properly formatted responses."""
        client, user = authenticated_client
        
        response = client.get("/user/protected")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
        
        # Ensure valid JSON response
        data = response.json()
        assert isinstance(data, dict)
