"""
Tests for dashboard controller functionality.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.controllers.dashboard_controller import DashboardController
from app.schemas.analytics import (
    UserSearchFilters,
    BulkUserOperation,
    UserExportRequest
)
from app.models.user import User
from tests.factories import UserFactory


class TestDashboardController:
    """Test dashboard controller methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.controller = DashboardController()

    def test_get_dashboard_statistics_success(self, db_session: Session):
        """Test successful dashboard statistics retrieval."""
        # Create admin user
        admin_user = UserFactory(role="admin", is_active=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create some test users
        user1 = UserFactory(role="user", is_active=True)
        user2 = UserFactory(role="user", is_active=False)
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Get dashboard stats
        stats = self.controller.get_dashboard_statistics(db_session, admin_user)
        
        assert stats.total_users >= 3
        assert stats.active_users >= 2
        assert stats.inactive_users >= 1
        assert stats.admin_users >= 1

    def test_get_dashboard_statistics_non_admin(self, db_session: Session):
        """Test dashboard statistics access denied for non-admin."""
        # Create regular user
        regular_user = UserFactory(role="user")
        db_session.add(regular_user)
        db_session.commit()
        
        # Should raise HTTPException for non-admin
        with pytest.raises(HTTPException) as exc_info:
            self.controller.get_dashboard_statistics(db_session, regular_user)
        
        assert exc_info.value.status_code == 403
        assert "admin access required" in exc_info.value.detail.lower()

    def test_get_dashboard_statistics_unauthenticated(self, db_session: Session):
        """Test dashboard statistics access denied for unauthenticated user."""
        with pytest.raises(HTTPException) as exc_info:
            self.controller.get_dashboard_statistics(db_session, None)
        
        assert exc_info.value.status_code == 401

    def test_search_users_success(self, db_session: Session):
        """Test successful user search."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Create test users to search
        user1 = UserFactory(username="john_doe", role="user")
        user2 = UserFactory(username="jane_smith", role="admin")
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Search users
        filters = UserSearchFilters(query="john", skip=0, limit=10)
        result = self.controller.search_users(db_session, admin_user, filters)
        
        assert result.total_count >= 1
        assert len(result.users) >= 1

    def test_search_users_non_admin(self, db_session: Session):
        """Test user search access denied for non-admin."""
        # Create regular user
        regular_user = UserFactory(role="user")
        db_session.add(regular_user)
        db_session.commit()
        
        filters = UserSearchFilters(skip=0, limit=10)
        
        with pytest.raises(HTTPException) as exc_info:
            self.controller.search_users(db_session, regular_user, filters)
        
        assert exc_info.value.status_code == 403

    def test_search_users_with_filters(self, db_session: Session):
        """Test user search with various filters."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Create test users
        active_user = UserFactory(role="user", is_active=True)
        inactive_user = UserFactory(role="user", is_active=False)
        admin_user2 = UserFactory(role="admin", is_active=True)
        
        db_session.add_all([active_user, inactive_user, admin_user2])
        db_session.commit()
        
        # Test role filter
        role_filters = UserSearchFilters(role="admin", skip=0, limit=10)
        result = self.controller.search_users(db_session, admin_user, role_filters)
        
        assert result.total_count >= 2  # At least 2 admin users
        assert all(user["role"] == "admin" for user in result.users)
        
        # Test status filter
        status_filters = UserSearchFilters(is_active=False, skip=0, limit=10)
        result = self.controller.search_users(db_session, admin_user, status_filters)
        
        assert result.total_count >= 1
        assert all(user["is_active"] is False for user in result.users)

    def test_bulk_activate_users_success(self, db_session: Session):
        """Test successful bulk user activation."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Create inactive users
        user1 = UserFactory(is_active=False)
        user2 = UserFactory(is_active=False)
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Bulk activate
        operation = BulkUserOperation(user_ids=[user1.id, user2.id], operation="activate")
        result = self.controller.bulk_user_operation(db_session, admin_user, operation)
        
        assert result.success_count == 2
        assert result.failure_count == 0
        assert user1.id in result.successful
        assert user2.id in result.successful

    def test_bulk_deactivate_users_success(self, db_session: Session):
        """Test successful bulk user deactivation."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Create active users
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=True)
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Bulk deactivate
        operation = BulkUserOperation(user_ids=[user1.id, user2.id], operation="deactivate")
        result = self.controller.bulk_user_operation(db_session, admin_user, operation)
        
        assert result.success_count == 2
        assert result.failure_count == 0

    def test_bulk_operation_non_admin(self, db_session: Session):
        """Test bulk operation access denied for non-admin."""
        # Create regular user
        regular_user = UserFactory(role="user")
        db_session.add(regular_user)
        db_session.commit()
        
        operation = BulkUserOperation(user_ids=[1], operation="activate")
        
        with pytest.raises(HTTPException) as exc_info:
            self.controller.bulk_user_operation(db_session, regular_user, operation)
        
        assert exc_info.value.status_code == 403

    def test_bulk_operation_invalid_operation(self, db_session: Session):
        """Test bulk operation with invalid operation type."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        operation = BulkUserOperation(user_ids=[1], operation="invalid_op")
        
        with pytest.raises(HTTPException) as exc_info:
            self.controller.bulk_user_operation(db_session, admin_user, operation)
        
        assert exc_info.value.status_code == 400
        assert "invalid operation" in exc_info.value.detail.lower()

    def test_bulk_operation_prevent_self_modification(self, db_session: Session):
        """Test bulk operation prevents admin from modifying themselves."""
        # Create admin user
        admin_user = UserFactory(role="admin", is_active=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Try to deactivate self
        operation = BulkUserOperation(user_ids=[admin_user.id], operation="deactivate")
        result = self.controller.bulk_user_operation(db_session, admin_user, operation)
        
        assert result.success_count == 0
        assert result.failure_count == 1
        assert any(failed["user_id"] == admin_user.id for failed in result.failed)

    def test_export_users_csv_success(self, db_session: Session):
        """Test successful CSV export."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Create test users
        user1 = UserFactory(username="john_doe")
        user2 = UserFactory(username="jane_smith")
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Export CSV
        export_request = UserExportRequest(format="csv")
        csv_content = self.controller.export_users(db_session, admin_user, export_request)
        
        assert isinstance(csv_content, str)
        assert "john_doe" in csv_content
        assert "jane_smith" in csv_content

    def test_export_users_json_success(self, db_session: Session):
        """Test successful JSON export."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Create test users
        user1 = UserFactory(username="test_user1")
        user2 = UserFactory(username="test_user2")
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Export JSON
        export_request = UserExportRequest(format="json")
        json_content = self.controller.export_users(db_session, admin_user, export_request)
        
        assert isinstance(json_content, str)
        assert "test_user1" in json_content
        assert "test_user2" in json_content

    def test_export_users_non_admin(self, db_session: Session):
        """Test user export access denied for non-admin."""
        # Create regular user
        regular_user = UserFactory(role="user")
        db_session.add(regular_user)
        db_session.commit()
        
        export_request = UserExportRequest(format="csv")
        
        with pytest.raises(HTTPException) as exc_info:
            self.controller.export_users(db_session, regular_user, export_request)
        
        assert exc_info.value.status_code == 403

    def test_export_users_invalid_format(self, db_session: Session):
        """Test user export with invalid format."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        export_request = UserExportRequest(format="xml")
        
        with pytest.raises(HTTPException) as exc_info:
            self.controller.export_users(db_session, admin_user, export_request)
        
        assert exc_info.value.status_code == 400
        assert "unsupported format" in exc_info.value.detail.lower()

    def test_export_users_with_filters(self, db_session: Session):
        """Test user export with filters applied."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Create test users with different roles
        admin_user2 = UserFactory(role="admin", username="admin2")
        regular_user = UserFactory(role="user", username="user1")
        db_session.add_all([admin_user2, regular_user])
        db_session.commit()
        
        # Export only admin users
        filters = UserSearchFilters(role="admin")
        export_request = UserExportRequest(format="csv", filters=filters)
        csv_content = self.controller.export_users(db_session, admin_user, export_request)
        
        assert "admin2" in csv_content
        # Regular user should not be in filtered export
        lines = csv_content.split('\n')
        user_lines = [line for line in lines if "user1" in line]
        assert len(user_lines) == 0


class TestDashboardControllerEdgeCases:
    """Test edge cases and error conditions for dashboard controller."""

    def setup_method(self):
        """Set up test fixtures."""
        self.controller = DashboardController()

    def test_search_users_invalid_pagination(self, db_session: Session):
        """Test search with invalid pagination parameters."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Test negative skip - this should be caught by Pydantic validation
        with pytest.raises(Exception):  # Pydantic ValidationError
            filters = UserSearchFilters(skip=-1, limit=10)
        
        # Test zero limit - this should be caught by Pydantic validation
        with pytest.raises(Exception):  # Pydantic ValidationError
            filters = UserSearchFilters(skip=0, limit=0)
        
        # Test excessive limit - this should be caught by Pydantic validation
        with pytest.raises(Exception):  # Pydantic ValidationError
            filters = UserSearchFilters(skip=0, limit=2000)
        
        # Test valid filters but check controller validation
        filters = UserSearchFilters(skip=0, limit=500)
        # This should work fine
        result = self.controller.search_users(db_session, admin_user, filters)
        assert isinstance(result.total_count, int)

    def test_bulk_operation_empty_user_ids(self, db_session: Session):
        """Test bulk operation with empty user ID list."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        operation = BulkUserOperation(user_ids=[], operation="activate")
        
        with pytest.raises(HTTPException) as exc_info:
            self.controller.bulk_user_operation(db_session, admin_user, operation)
        
        assert exc_info.value.status_code == 400
        assert "no user ids provided" in exc_info.value.detail.lower()

    def test_bulk_operation_too_many_users(self, db_session: Session):
        """Test bulk operation with too many users."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Try to operate on too many users at once
        user_ids = list(range(1, 102))  # 101 user IDs
        operation = BulkUserOperation(user_ids=user_ids, operation="activate")
        
        with pytest.raises(HTTPException) as exc_info:
            self.controller.bulk_user_operation(db_session, admin_user, operation)
        
        assert exc_info.value.status_code == 400
        assert "too many users" in exc_info.value.detail.lower()

    def test_dashboard_stats_database_error(self, db_session: Session):
        """Test dashboard statistics handling database errors gracefully."""
        # Create admin user
        admin_user = UserFactory(role="admin")
        db_session.add(admin_user)
        db_session.commit()
        
        # Mock database error
        with pytest.raises(Exception):
            # Simulate database connection error
            db_session.close()
            self.controller.get_dashboard_statistics(db_session, admin_user)
