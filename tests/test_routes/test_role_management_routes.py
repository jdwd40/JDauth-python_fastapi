"""
Test module for role management API routes using TDD approach.

This module tests the API endpoints for role management including:
- Role assignment endpoints
- User status management endpoints  
- Admin authorization checks
- Safety checks for admin operations
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import create_user_in_db


class TestRoleAssignmentRoutes:
    """Test cases for role assignment API routes."""

    def test_assign_admin_role_success(self, client: TestClient, db_session: Session):
        """Test successful admin role assignment by admin user."""
        # Create admin and regular user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        regular_user = create_user_in_db(db_session, username="user", role="user")
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Assign admin role to regular user
        response = client.put(
            f"/api/admin/users/{regular_user.id}/role",
            json={"role": "admin"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert data["username"] == "user"
        
        # Clean up
        app.dependency_overrides.clear()

    def test_assign_user_role_success(self, client: TestClient, db_session: Session):
        """Test successful user role assignment (demotion) by admin user."""
        # Create admin users
        admin_user = create_user_in_db(db_session, username="admin1", role="admin")
        target_admin = create_user_in_db(db_session, username="admin2", role="admin")
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Demote admin to user role
        response = client.put(
            f"/api/admin/users/{target_admin.id}/role",
            json={"role": "user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "user"
        assert data["username"] == "admin2"
        
        # Clean up
        app.dependency_overrides.clear()

    def test_assign_invalid_role_fails(self, client: TestClient, db_session: Session):
        """Test that assigning invalid role returns 400."""
        # Create admin and regular user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        regular_user = create_user_in_db(db_session, username="user", role="user")
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Try to assign invalid role
        response = client.put(
            f"/api/admin/users/{regular_user.id}/role",
            json={"role": "superadmin"}
        )
        
        # Pydantic validation returns 422, not 400
        assert response.status_code == 422
        error_response = response.json()
        # For validation errors, the format is different
        assert "detail" in error_response
        
        # Clean up
        app.dependency_overrides.clear()

    def test_assign_role_to_nonexistent_user_fails(self, client: TestClient, db_session: Session):
        """Test that assigning role to non-existent user returns 404."""
        # Create admin user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Try to assign role to non-existent user
        response = client.put(
            "/api/admin/users/99999/role",
            json={"role": "admin"}
        )
        
        assert response.status_code == 404
        error_response = response.json()
        # The error format might be {"error": True, "message": "...", ...} or {"detail": "..."}
        error_message = error_response.get("detail") or error_response.get("message", "")
        assert "User not found" in error_message
        
        # Clean up
        app.dependency_overrides.clear()

    def test_admin_cannot_modify_own_role(self, client: TestClient, db_session: Session):
        """Test that admin cannot modify their own role."""
        # Create admin user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Try to demote self
        response = client.put(
            f"/api/admin/users/{admin_user.id}/role",
            json={"role": "user"}
        )
        
        assert response.status_code == 403
        error_response = response.json()
        error_message = error_response.get("detail") or error_response.get("message", "")
        assert "Cannot modify your own role" in error_message
        
        # Clean up
        app.dependency_overrides.clear()

    def test_regular_user_cannot_assign_roles(self, client: TestClient, db_session: Session):
        """Test that regular users cannot assign roles."""
        # Create regular users
        regular_user = create_user_in_db(db_session, username="user1", role="user")
        target_user = create_user_in_db(db_session, username="user2", role="user")
        
        # Override auth to use regular user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return regular_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Try to assign admin role
        response = client.put(
            f"/api/admin/users/{target_user.id}/role",
            json={"role": "admin"}
        )
        
        assert response.status_code == 403
        error_response = response.json()
        error_message = error_response.get("detail") or error_response.get("message", "")
        assert "Admin access required" in error_message
        
        # Clean up
        app.dependency_overrides.clear()


class TestUserStatusRoutes:
    """Test cases for user status management API routes."""

    def test_deactivate_user_success(self, client: TestClient, db_session: Session):
        """Test successful user deactivation by admin."""
        # Create admin and regular user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        regular_user = create_user_in_db(db_session, username="user", role="user")
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Deactivate user
        response = client.put(
            f"/api/admin/users/{regular_user.id}/status",
            json={"is_active": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["username"] == "user"
        
        # Clean up
        app.dependency_overrides.clear()

    def test_activate_user_success(self, client: TestClient, db_session: Session):
        """Test successful user activation by admin."""
        # Create admin and inactive user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        inactive_user = create_user_in_db(db_session, username="user", role="user", is_active=False)
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Activate user
        response = client.put(
            f"/api/admin/users/{inactive_user.id}/status",
            json={"is_active": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
        assert data["username"] == "user"
        
        # Clean up
        app.dependency_overrides.clear()

    def test_admin_cannot_deactivate_self(self, client: TestClient, db_session: Session):
        """Test that admin cannot deactivate themselves."""
        # Create admin user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Try to deactivate self
        response = client.put(
            f"/api/admin/users/{admin_user.id}/status",
            json={"is_active": False}
        )
        
        assert response.status_code == 403
        error_response = response.json()
        error_message = error_response.get("detail") or error_response.get("message", "")
        assert "Cannot modify your own status" in error_message
        
        # Clean up
        app.dependency_overrides.clear()

    def test_set_status_for_nonexistent_user_fails(self, client: TestClient, db_session: Session):
        """Test that setting status for non-existent user returns 404."""
        # Create admin user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Try to set status for non-existent user
        response = client.put(
            "/api/admin/users/99999/status",
            json={"is_active": False}
        )
        
        assert response.status_code == 404
        error_response = response.json()
        error_message = error_response.get("detail") or error_response.get("message", "")
        assert "User not found" in error_message
        
        # Clean up
        app.dependency_overrides.clear()

    def test_regular_user_cannot_modify_status(self, client: TestClient, db_session: Session):
        """Test that regular users cannot modify user status."""
        # Create regular users
        regular_user = create_user_in_db(db_session, username="user1", role="user")
        target_user = create_user_in_db(db_session, username="user2", role="user")
        
        # Override auth to use regular user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return regular_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Try to deactivate another user
        response = client.put(
            f"/api/admin/users/{target_user.id}/status",
            json={"is_active": False}
        )
        
        assert response.status_code == 403
        error_response = response.json()
        error_message = error_response.get("detail") or error_response.get("message", "")
        assert "Admin access required" in error_message
        
        # Clean up
        app.dependency_overrides.clear()


class TestUserListingWithRolesAndStatus:
    """Test cases for user listing with role and status filtering."""

    def test_list_users_includes_role_and_status(self, client: TestClient, db_session: Session):
        """Test that user listing includes role and status information."""
        # Create admin user and various other users
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        create_user_in_db(db_session, username="user1", role="user", is_active=True)
        create_user_in_db(db_session, username="user2", role="user", is_active=False)
        create_user_in_db(db_session, username="admin2", role="admin", is_active=True)
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Get user list
        response = client.get("/api/users")
        
        assert response.status_code == 200
        users = response.json()
        
        # Check that role and is_active fields are included
        for user in users:
            assert "role" in user
            assert "is_active" in user
            assert user["role"] in ["user", "admin"]
            assert isinstance(user["is_active"], bool)
        
        # Clean up
        app.dependency_overrides.clear()

    def test_filter_users_by_role(self, client: TestClient, db_session: Session):
        """Test filtering users by role."""
        # Create admin user and various other users
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        create_user_in_db(db_session, username="user1", role="user")
        create_user_in_db(db_session, username="user2", role="user")
        create_user_in_db(db_session, username="admin2", role="admin")
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Get only admin users
        response = client.get("/api/users?role=admin")
        
        assert response.status_code == 200
        users = response.json()
        
        # All returned users should be admins
        for user in users:
            assert user["role"] == "admin"
        
        # Should have 2 admin users
        assert len(users) == 2
        
        # Clean up
        app.dependency_overrides.clear()

    def test_filter_users_by_status(self, client: TestClient, db_session: Session):
        """Test filtering users by active status."""
        # Create admin user and various other users
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        create_user_in_db(db_session, username="active1", role="user", is_active=True)
        create_user_in_db(db_session, username="active2", role="user", is_active=True)
        create_user_in_db(db_session, username="inactive1", role="user", is_active=False)
        
        # Override auth to use admin user
        from app.utils.dependencies import get_current_user
        from app.main import app
        
        def override_get_current_user():
            return admin_user
        
        app.dependency_overrides[get_current_user] = override_get_current_user
        
        # Get only inactive users
        response = client.get("/api/users?is_active=false")
        
        assert response.status_code == 200
        users = response.json()
        
        # All returned users should be inactive
        for user in users:
            assert user["is_active"] is False
        
        # Should have 1 inactive user
        assert len(users) == 1
        assert users[0]["username"] == "inactive1"
        
        # Clean up
        app.dependency_overrides.clear()
