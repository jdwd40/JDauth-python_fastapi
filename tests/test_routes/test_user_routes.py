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
        
        response = client.get("/api/user/profile")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert data["username"] == user.username
        assert "created_at" in data

    def test_get_profile_unauthorized(self, client: TestClient):
        """Test profile retrieval without authentication fails."""
        response = client.get("/api/user/profile")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "message" in data

    def test_get_profile_invalid_token(self, client: TestClient):
        """Test profile retrieval with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/user/profile", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "message" in data

    def test_update_profile_success(self, authenticated_client):
        """Test successful profile update."""
        client, user = authenticated_client
        
        update_data = {
            "username": "newusername"
        }
        
        response = client.put("/api/user/profile", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert "username" in data

    def test_update_profile_unauthorized(self, client: TestClient):
        """Test profile update without authentication fails."""
        update_data = {"username": "newusername"}
        
        response = client.put("/api/user/profile", json=update_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "message" in data

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
            response = client.put("/api/user/profile", json=update_data)
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_protected_endpoint_success(self, authenticated_client):
        """Test successful access to protected endpoint."""
        client, user = authenticated_client
        
        response = client.get("/api/user/protected")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert user.username in data["message"]

    def test_protected_endpoint_unauthorized(self, client: TestClient):
        """Test protected endpoint without authentication fails."""
        response = client.get("/api/user/protected")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "message" in data

    def test_get_users_list_success_admin(self, admin_client):
        """Test successful retrieval of users list by admin."""
        client, admin_user = admin_client
        
        response = client.get("/api/users")
        
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
        
        response = client.get("/api/users?skip=0&limit=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # Should return at most 5 users due to limit
        assert len(data) <= 5

    def test_get_users_list_forbidden_non_admin(self, authenticated_client):
        """Test users list access denied for non-admin users."""
        client, regular_user = authenticated_client
        
        response = client.get("/api/users")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "message" in data
        assert "admin" in data["message"].lower()

    def test_get_users_list_unauthorized(self, client: TestClient):
        """Test users list without authentication fails."""
        response = client.get("/api/users")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "message" in data

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
            response = client.get(f"/api/users{params}")
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_user_routes_error_handling(self, client: TestClient):
        """Test proper error handling in user routes."""
        # Test with malformed requests
        headers = {"Authorization": "Bearer valid_token"}
        
        # Invalid JSON for profile update
        response = client.put(
            "/api/user/profile",
            data="invalid json",
            headers={**headers, "Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_user_routes_response_format(self, authenticated_client):
        """Test that user routes return properly formatted responses."""
        client, user = authenticated_client
        
        response = client.get("/api/user/protected")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
        
        # Ensure valid JSON response
        data = response.json()
        assert isinstance(data, dict)


class TestAdminUserCRUDRoutes:
    """Test suite for admin user CRUD operations."""

    # POST /api/admin/users tests
    def test_admin_create_user_success(self, admin_client):
        """Test successful user creation by admin."""
        client, admin_user = admin_client
        
        user_data = {
            "username": "newuser123",
            "password": "securepassword123"
        }
        
        response = client.post("/api/admin/users", json=user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["username"] == user_data["username"]
        assert "created_at" in data
        assert "password" not in data  # Should not return password
        assert "hashed_password" not in data  # Should not return hashed password

    def test_admin_create_user_duplicate_username(self, admin_client, db_session):
        """Test admin user creation with duplicate username fails."""
        client, admin_user = admin_client
        
        # Create existing user
        from tests.factories import create_user_in_db
        existing_user = create_user_in_db(db_session, username="existinguser")
        
        user_data = {
            "username": "existinguser",
            "password": "securepassword123"
        }
        
        response = client.post("/api/admin/users", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "message" in data
        assert "username already exists" in data["message"].lower()

    def test_admin_create_user_invalid_data(self, admin_client):
        """Test admin user creation with invalid data fails."""
        client, admin_user = admin_client
        
        test_cases = [
            # Missing username
            {"password": "password123"},
            # Missing password
            {"username": "testuser"},
            # Empty username
            {"username": "", "password": "password123"},
            # Short password
            {"username": "testuser", "password": "123"},
            # Short username
            {"username": "ab", "password": "password123"},
            # Invalid data types
            {"username": 123, "password": "password123"},
            {"username": "testuser", "password": 123},
        ]
        
        for user_data in test_cases:
            response = client.post("/api/admin/users", json=user_data)
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_admin_create_user_unauthorized(self, client):
        """Test user creation without authentication fails."""
        user_data = {
            "username": "newuser123",
            "password": "securepassword123"
        }
        
        response = client.post("/api/admin/users", json=user_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_create_user_forbidden_non_admin(self, authenticated_client):
        """Test user creation by non-admin user fails."""
        client, regular_user = authenticated_client
        
        user_data = {
            "username": "newuser123",
            "password": "securepassword123"
        }
        
        response = client.post("/api/admin/users", json=user_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # GET /api/admin/users/{id} tests
    def test_admin_get_user_by_id_success(self, admin_client, db_session):
        """Test successful retrieval of user by ID by admin."""
        client, admin_user = admin_client
        
        # Create test user
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        response = client.get(f"/api/admin/users/{test_user.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_admin_get_user_by_id_not_found(self, admin_client):
        """Test retrieval of non-existent user by admin."""
        client, admin_user = admin_client
        
        response = client.get("/api/admin/users/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "message" in data

    def test_admin_get_user_by_id_invalid_id(self, admin_client):
        """Test retrieval with invalid user ID."""
        client, admin_user = admin_client
        
        test_cases = ["abc", "0", "-1", "1.5"]
        
        for invalid_id in test_cases:
            response = client.get(f"/api/admin/users/{invalid_id}")
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_admin_get_user_by_id_unauthorized(self, client, db_session):
        """Test user retrieval without authentication fails."""
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        response = client.get(f"/api/admin/users/{test_user.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_get_user_by_id_forbidden_non_admin(self, authenticated_client, db_session):
        """Test user retrieval by non-admin user fails."""
        client, regular_user = authenticated_client
        
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        response = client.get(f"/api/admin/users/{test_user.id}")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # PUT /api/admin/users/{id} tests
    def test_admin_update_user_success(self, admin_client, db_session):
        """Test successful user update by admin."""
        client, admin_user = admin_client
        
        # Create test user
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        update_data = {
            "username": "updateduser123",
            "password": "newpassword123"
        }
        
        response = client.put(f"/api/admin/users/{test_user.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["username"] == update_data["username"]
        assert "created_at" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_admin_update_user_partial_success(self, admin_client, db_session):
        """Test successful partial user update by admin."""
        client, admin_user = admin_client
        
        # Create test user
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        original_username = test_user.username
        
        # Update only username
        update_data = {"username": "partialupdateuser"}
        
        response = client.put(f"/api/admin/users/{test_user.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == update_data["username"]
        
        # Update only password
        update_data = {"password": "newpassword123"}
        
        response = client.put(f"/api/admin/users/{test_user.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK

    def test_admin_update_user_not_found(self, admin_client):
        """Test update of non-existent user by admin."""
        client, admin_user = admin_client
        
        update_data = {"username": "updateduser"}
        
        response = client.put("/api/admin/users/99999", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_update_user_duplicate_username(self, admin_client, db_session):
        """Test admin user update with duplicate username fails."""
        client, admin_user = admin_client
        
        # Create two test users
        from tests.factories import create_user_in_db
        user1 = create_user_in_db(db_session, username="user1")
        user2 = create_user_in_db(db_session, username="user2")
        
        # Try to update user2's username to user1's username
        update_data = {"username": "user1"}
        
        response = client.put(f"/api/admin/users/{user2.id}", json=update_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "username already exists" in data["message"].lower()

    def test_admin_update_user_invalid_data(self, admin_client, db_session):
        """Test admin user update with invalid data fails."""
        client, admin_user = admin_client
        
        # Create test user
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        test_cases = [
            # Empty username
            {"username": ""},
            # Short password
            {"password": "123"},
            # Short username
            {"username": "ab"},
            # Invalid data types
            {"username": 123},
            {"password": 123},
        ]
        
        for update_data in test_cases:
            response = client.put(f"/api/admin/users/{test_user.id}", json=update_data)
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_admin_update_user_unauthorized(self, client, db_session):
        """Test user update without authentication fails."""
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        update_data = {"username": "updateduser"}
        
        response = client.put(f"/api/admin/users/{test_user.id}", json=update_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_update_user_forbidden_non_admin(self, authenticated_client, db_session):
        """Test user update by non-admin user fails."""
        client, regular_user = authenticated_client
        
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        update_data = {"username": "updateduser"}
        
        response = client.put(f"/api/admin/users/{test_user.id}", json=update_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_update_self_prevention(self, admin_client):
        """Test that admin cannot modify their own account (safety check)."""
        client, admin_user = admin_client
        
        update_data = {"username": "selfupdated"}
        
        response = client.put(f"/api/admin/users/{admin_user.id}", json=update_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "cannot modify your own account" in data["message"].lower()

    # DELETE /api/admin/users/{id} tests
    def test_admin_delete_user_success(self, admin_client, db_session):
        """Test successful user deletion by admin."""
        client, admin_user = admin_client
        
        # Create test user
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        response = client.delete(f"/api/admin/users/{test_user.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "deleted successfully" in data["message"].lower()

    def test_admin_delete_user_not_found(self, admin_client):
        """Test deletion of non-existent user by admin."""
        client, admin_user = admin_client
        
        response = client.delete("/api/admin/users/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_delete_user_invalid_id(self, admin_client):
        """Test deletion with invalid user ID."""
        client, admin_user = admin_client
        
        test_cases = ["abc", "0", "-1", "1.5"]
        
        for invalid_id in test_cases:
            response = client.delete(f"/api/admin/users/{invalid_id}")
            assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_admin_delete_user_unauthorized(self, client, db_session):
        """Test user deletion without authentication fails."""
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        response = client.delete(f"/api/admin/users/{test_user.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_admin_delete_user_forbidden_non_admin(self, authenticated_client, db_session):
        """Test user deletion by non-admin user fails."""
        client, regular_user = authenticated_client
        
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="targetuser")
        
        response = client.delete(f"/api/admin/users/{test_user.id}")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_delete_self_prevention(self, admin_client):
        """Test that admin cannot delete their own account (safety check)."""
        client, admin_user = admin_client
        
        response = client.delete(f"/api/admin/users/{admin_user.id}")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "cannot delete your own account" in data["message"].lower()

    # Additional edge case tests
    def test_admin_crud_operations_response_format(self, admin_client, db_session):
        """Test that admin CRUD operations return properly formatted responses."""
        client, admin_user = admin_client
        
        # Test POST response format
        user_data = {"username": "formatuser", "password": "password123"}
        response = client.post("/api/admin/users", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.headers["content-type"] == "application/json"
        
        # Test GET response format
        from tests.factories import create_user_in_db
        test_user = create_user_in_db(db_session, username="formatuser2")
        response = client.get(f"/api/admin/users/{test_user.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"

    def test_admin_crud_operations_error_handling(self, admin_client):
        """Test proper error handling in admin CRUD operations."""
        client, admin_user = admin_client
        
        # Test with malformed JSON
        response = client.post(
            "/api/admin/users",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
