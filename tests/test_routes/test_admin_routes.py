"""
Tests for admin routes functionality including dashboard and user management.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.factories import UserFactory


class TestAdminDashboardRoutes:
    """Test admin dashboard-related routes."""

    def test_get_dashboard_stats_success(self, admin_client, db_session: Session):
        """Test successful dashboard statistics retrieval."""
        client, admin_user = admin_client
        
        # Create some test users
        user1 = UserFactory(role="user", is_active=True)
        user2 = UserFactory(role="user", is_active=False)
        user3 = UserFactory(role="admin", is_active=True)
        
        db_session.add_all([user1, user2, user3])
        db_session.commit()
        
        # Get dashboard stats
        response = client.get("/api/admin/dashboard/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_users" in data
        assert "active_users" in data
        assert "inactive_users" in data
        assert "admin_users" in data
        assert "recent_registrations" in data
        assert "user_growth" in data
        
        assert data["total_users"] >= 4  # admin + 3 created users
        assert data["active_users"] >= 3
        assert data["inactive_users"] >= 1
        assert data["admin_users"] >= 2

    def test_get_dashboard_stats_non_admin(self, authenticated_client):
        """Test dashboard stats access denied for non-admin."""
        client, user = authenticated_client
        
        response = client.get("/api/admin/dashboard/stats")
        
        assert response.status_code == 403
        assert "admin access required" in response.json()["message"].lower()

    def test_get_dashboard_stats_unauthenticated(self, client: TestClient):
        """Test dashboard stats access denied for unauthenticated user."""
        response = client.get("/api/admin/dashboard/stats")
        
        assert response.status_code == 401


class TestAdminUserSearchRoutes:
    """Test admin user search routes."""

    def test_search_users_basic(self, admin_client, db_session: Session):
        """Test basic user search functionality."""
        client, admin_user = admin_client
        
        # Create test users
        user1 = UserFactory(username="john_doe", role="user")
        user2 = UserFactory(username="jane_smith", role="user")
        user3 = UserFactory(username="bob_johnson", role="user")
        
        db_session.add_all([user1, user2, user3])
        db_session.commit()
        
        # Search for users containing "john"
        response = client.get("/api/admin/users/search?query=john")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data
        assert "total_count" in data
        assert "page_info" in data
        
        assert data["total_count"] >= 1
        assert len(data["users"]) >= 1
        assert any("john" in user["username"].lower() for user in data["users"])

    def test_search_users_with_role_filter(self, admin_client, db_session: Session):
        """Test user search with role filtering."""
        client, admin_user = admin_client
        
        # Create test users with different roles
        admin_user2 = UserFactory(role="admin", username="admin2")
        regular_user1 = UserFactory(role="user", username="user1")
        regular_user2 = UserFactory(role="user", username="user2")
        
        db_session.add_all([admin_user2, regular_user1, regular_user2])
        db_session.commit()
        
        # Search for admin users only
        response = client.get("/api/admin/users/search?role=admin")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] >= 2  # admin_user + admin_user2
        assert all(user["role"] == "admin" for user in data["users"])

    def test_search_users_with_status_filter(self, admin_client, db_session: Session):
        """Test user search with status filtering."""
        client, admin_user = admin_client
        
        # Create test users with different statuses
        active_user = UserFactory(is_active=True, username="active_user")
        inactive_user = UserFactory(is_active=False, username="inactive_user")
        
        db_session.add_all([active_user, inactive_user])
        db_session.commit()
        
        # Search for inactive users only
        response = client.get("/api/admin/users/search?is_active=false")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] >= 1
        assert all(user["is_active"] is False for user in data["users"])

    def test_search_users_with_date_filter(self, admin_client, db_session: Session):
        """Test user search with date filtering."""
        client, admin_user = admin_client
        
        # Create users with specific dates
        recent_date = datetime.now(timezone.utc) - timedelta(days=1)
        old_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        recent_user = UserFactory(username="recent_user")
        recent_user.created_at = recent_date
        
        old_user = UserFactory(username="old_user")
        old_user.created_at = old_date
        
        db_session.add_all([recent_user, old_user])
        db_session.commit()
        
        # Search for users created in the last week
        created_after = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")
        response = client.get(f"/api/admin/users/search?created_after={created_after}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] >= 1
        # Verify all returned users were created after the filter date
        for user in data["users"]:
            user_date = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
            assert user_date >= datetime.fromisoformat(created_after.replace("Z", "+00:00"))

    def test_search_users_pagination(self, admin_client, db_session: Session):
        """Test user search pagination."""
        client, admin_user = admin_client
        
        # Create multiple test users
        users = [UserFactory(username=f"testuser{i}") for i in range(5)]
        db_session.add_all(users)
        db_session.commit()
        
        # Test first page with limit of 2
        response = client.get("/api/admin/users/search?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["users"]) <= 2
        assert data["total_count"] >= 5
        assert data["page_info"]["current_page"] == 1
        assert data["page_info"]["has_next"] is True
        
        # Test second page
        response = client.get("/api/admin/users/search?skip=2&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page_info"]["current_page"] == 2
        assert data["page_info"]["has_previous"] is True

    def test_search_users_sorting(self, admin_client, db_session: Session):
        """Test user search sorting."""
        client, admin_user = admin_client
        
        # Create users with different creation dates
        user1 = UserFactory(username="user_a")
        user1.created_at = datetime.now(timezone.utc) - timedelta(days=2)
        
        user2 = UserFactory(username="user_b")
        user2.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Test ascending sort by creation date
        response = client.get("/api/admin/users/search?sort_by=created_at&sort_order=asc")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify sorting (oldest first)
        if len(data["users"]) >= 2:
            dates = [datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")) 
                    for user in data["users"]]
            assert dates == sorted(dates)

    def test_search_users_non_admin(self, authenticated_client):
        """Test user search access denied for non-admin."""
        client, user = authenticated_client
        
        response = client.get("/api/admin/users/search")
        
        assert response.status_code == 403
        assert "admin access required" in response.json()["message"].lower()

    def test_search_users_invalid_parameters(self, admin_client):
        """Test user search with invalid parameters."""
        client, admin_user = admin_client
        
        # Test negative skip - FastAPI returns 422 for validation errors
        response = client.get("/api/admin/users/search?skip=-1")
        assert response.status_code == 422
        
        # Test zero limit - FastAPI returns 422 for validation errors
        response = client.get("/api/admin/users/search?limit=0")
        assert response.status_code == 422
        
        # Test excessive limit - FastAPI returns 422 for validation errors
        response = client.get("/api/admin/users/search?limit=2000")
        assert response.status_code == 422


class TestAdminBulkOperationsRoutes:
    """Test admin bulk operations routes."""

    def test_bulk_activate_users_success(self, admin_client, db_session: Session):
        """Test successful bulk user activation."""
        client, admin_user = admin_client
        
        # Create inactive test users
        user1 = UserFactory(is_active=False)
        user2 = UserFactory(is_active=False)
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Bulk activate users
        payload = {
            "user_ids": [user1.id, user2.id],
            "operation": "activate"
        }
        
        response = client.post("/api/admin/users/bulk", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success_count"] == 2
        assert data["failure_count"] == 0
        assert user1.id in data["successful"]
        assert user2.id in data["successful"]

    def test_bulk_deactivate_users_success(self, admin_client, db_session: Session):
        """Test successful bulk user deactivation."""
        client, admin_user = admin_client
        
        # Create active test users
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=True)
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Bulk deactivate users
        payload = {
            "user_ids": [user1.id, user2.id],
            "operation": "deactivate"
        }
        
        response = client.post("/api/admin/users/bulk", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success_count"] == 2
        assert data["failure_count"] == 0

    def test_bulk_operation_with_nonexistent_users(self, admin_client, db_session: Session):
        """Test bulk operation with non-existent user IDs."""
        client, admin_user = admin_client
        
        user = UserFactory(is_active=False)
        db_session.add(user)
        db_session.commit()
        
        # Include non-existent user ID
        payload = {
            "user_ids": [user.id, 99999],
            "operation": "activate"
        }
        
        response = client.post("/api/admin/users/bulk", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success_count"] == 1
        assert data["failure_count"] == 1
        assert user.id in data["successful"]
        assert any(failed["user_id"] == 99999 for failed in data["failed"])

    def test_bulk_operation_prevent_self_modification(self, admin_client, db_session: Session):
        """Test bulk operation prevents admin from modifying themselves."""
        client, admin_user = admin_client
        
        # Try to deactivate self
        payload = {
            "user_ids": [admin_user.id],
            "operation": "deactivate"
        }
        
        response = client.post("/api/admin/users/bulk", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success_count"] == 0
        assert data["failure_count"] == 1
        assert any(failed["user_id"] == admin_user.id for failed in data["failed"])

    def test_bulk_operation_non_admin(self, authenticated_client):
        """Test bulk operation access denied for non-admin."""
        client, user = authenticated_client
        
        payload = {
            "user_ids": [1],
            "operation": "activate"
        }
        
        response = client.post("/api/admin/users/bulk", json=payload)
        
        assert response.status_code == 403

    def test_bulk_operation_invalid_operation(self, admin_client):
        """Test bulk operation with invalid operation type."""
        client, admin_user = admin_client
        
        payload = {
            "user_ids": [1],
            "operation": "invalid_operation"
        }
        
        response = client.post("/api/admin/users/bulk", json=payload)
        
        assert response.status_code == 400
        assert "invalid operation" in response.json()["message"].lower()

    def test_bulk_operation_empty_user_ids(self, admin_client):
        """Test bulk operation with empty user ID list."""
        client, admin_user = admin_client
        
        payload = {
            "user_ids": [],
            "operation": "activate"
        }
        
        response = client.post("/api/admin/users/bulk", json=payload)
        
        assert response.status_code == 400
        assert "no user ids provided" in response.json()["message"].lower()

    def test_bulk_operation_too_many_users(self, admin_client):
        """Test bulk operation with too many users."""
        client, admin_user = admin_client
        
        # Try to operate on too many users at once
        payload = {
            "user_ids": list(range(1, 102)),  # 101 user IDs
            "operation": "activate"
        }
        
        response = client.post("/api/admin/users/bulk", json=payload)
        
        assert response.status_code == 400
        assert "too many users" in response.json()["message"].lower()


class TestAdminUserExportRoutes:
    """Test admin user export routes."""

    def test_export_users_csv_success(self, admin_client, db_session: Session):
        """Test successful CSV export."""
        client, admin_user = admin_client
        
        # Create test users
        user1 = UserFactory(username="export_user1", role="user")
        user2 = UserFactory(username="export_user2", role="admin")
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Export to CSV
        payload = {"format": "csv"}
        response = client.post("/api/admin/users/export", json=payload)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        csv_content = response.text
        assert "export_user1" in csv_content
        assert "export_user2" in csv_content
        assert "username" in csv_content.lower()  # Header row

    def test_export_users_json_success(self, admin_client, db_session: Session):
        """Test successful JSON export."""
        client, admin_user = admin_client
        
        # Create test users
        user1 = UserFactory(username="json_user1")
        user2 = UserFactory(username="json_user2")
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Export to JSON
        payload = {"format": "json"}
        response = client.post("/api/admin/users/export", json=payload)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        json_content = response.text
        assert "json_user1" in json_content
        assert "json_user2" in json_content

    def test_export_users_with_filters(self, admin_client, db_session: Session):
        """Test user export with filters applied."""
        client, admin_user = admin_client
        
        # Create test users with different roles
        admin_user2 = UserFactory(role="admin", username="admin_export")
        regular_user = UserFactory(role="user", username="user_export")
        
        db_session.add_all([admin_user2, regular_user])
        db_session.commit()
        
        # Export only admin users
        payload = {
            "format": "csv",
            "filters": {"role": "admin"},
            "include_inactive": True
        }
        
        response = client.post("/api/admin/users/export", json=payload)
        
        assert response.status_code == 200
        csv_content = response.text
        
        assert "admin_export" in csv_content
        # Regular user should not be in filtered export
        lines = csv_content.split('\n')
        user_lines = [line for line in lines if "user_export" in line]
        assert len(user_lines) == 0

    def test_export_users_exclude_inactive(self, admin_client, db_session: Session):
        """Test user export excluding inactive users."""
        client, admin_user = admin_client
        
        # Create active and inactive users
        active_user = UserFactory(is_active=True, username="active_export")
        inactive_user = UserFactory(is_active=False, username="inactive_export")
        
        db_session.add_all([active_user, inactive_user])
        db_session.commit()
        
        # Export excluding inactive users
        payload = {
            "format": "csv",
            "include_inactive": False
        }
        
        response = client.post("/api/admin/users/export", json=payload)
        
        assert response.status_code == 200
        csv_content = response.text
        
        assert "active_export" in csv_content
        # Inactive user should not be included
        lines = csv_content.split('\n')
        inactive_lines = [line for line in lines if "inactive_export" in line]
        assert len(inactive_lines) == 0

    def test_export_users_non_admin(self, authenticated_client):
        """Test user export access denied for non-admin."""
        client, user = authenticated_client
        
        payload = {"format": "csv"}
        response = client.post("/api/admin/users/export", json=payload)
        
        assert response.status_code == 403

    def test_export_users_invalid_format(self, admin_client):
        """Test user export with invalid format."""
        client, admin_user = admin_client
        
        payload = {"format": "xml"}
        response = client.post("/api/admin/users/export", json=payload)
        
        assert response.status_code == 400
        assert "unsupported format" in response.json()["message"].lower()

    def test_export_users_unauthenticated(self, client: TestClient):
        """Test user export access denied for unauthenticated user."""
        payload = {"format": "csv"}
        response = client.post("/api/admin/users/export", json=payload)
        
        assert response.status_code == 401


class TestAdminRoutesIntegration:
    """Integration tests for admin routes."""

    def test_full_admin_workflow(self, admin_client, db_session: Session):
        """Test complete admin workflow: search, bulk operations, export."""
        client, admin_user = admin_client
        
        # Create test users
        active_users = [UserFactory(is_active=True, role="user") for _ in range(3)]
        inactive_users = [UserFactory(is_active=False, role="user") for _ in range(2)]
        
        db_session.add_all(active_users + inactive_users)
        db_session.commit()
        
        # 1. Get dashboard stats
        stats_response = client.get("/api/admin/dashboard/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        initial_active = stats["active_users"]
        initial_inactive = stats["inactive_users"]
        
        # 2. Search for inactive users
        search_response = client.get("/api/admin/users/search?is_active=false")
        assert search_response.status_code == 200
        search_data = search_response.json()
        
        inactive_user_ids = [user["id"] for user in search_data["users"]]
        assert len(inactive_user_ids) >= 2
        
        # 3. Bulk activate inactive users
        bulk_payload = {
            "user_ids": inactive_user_ids,
            "operation": "activate"
        }
        bulk_response = client.post("/api/admin/users/bulk", json=bulk_payload)
        assert bulk_response.status_code == 200
        bulk_data = bulk_response.json()
        
        assert bulk_data["success_count"] >= 2
        
        # 4. Verify stats changed
        new_stats_response = client.get("/api/admin/dashboard/stats")
        assert new_stats_response.status_code == 200
        new_stats = new_stats_response.json()
        
        assert new_stats["active_users"] > initial_active
        assert new_stats["inactive_users"] < initial_inactive
        
        # 5. Export all users
        export_payload = {"format": "csv"}
        export_response = client.post("/api/admin/users/export", json=export_payload)
        assert export_response.status_code == 200
        
        csv_content = export_response.text
        # Verify all users are in export
        for user in active_users + inactive_users:
            assert user.username in csv_content
