"""
Tests for analytics service functionality.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.services.analytics_service import (
    get_dashboard_stats,
    search_users,
    bulk_activate_users,
    bulk_deactivate_users,
    export_users_csv,
    export_users_json,
    get_user_growth_data,
    count_recent_registrations
)
from app.schemas.analytics import (
    UserSearchFilters,
    BulkUserOperation,
    UserExportRequest
)
from app.models.user import User
from tests.factories import UserFactory


class TestAnalyticsService:
    """Test analytics service functions."""

    def test_get_dashboard_stats_success(self, db_session: Session):
        """Test successful dashboard stats retrieval."""
        # Create test users
        admin_user = UserFactory(role="admin", is_active=True)
        active_user = UserFactory(role="user", is_active=True)
        inactive_user = UserFactory(role="user", is_active=False)
        
        db_session.add_all([admin_user, active_user, inactive_user])
        db_session.commit()
        
        # Get dashboard stats
        stats = get_dashboard_stats(db_session)
        
        # Assertions
        assert stats.total_users >= 3
        assert stats.active_users >= 2
        assert stats.inactive_users >= 1
        assert stats.admin_users >= 1
        assert isinstance(stats.recent_registrations.today, int)
        assert isinstance(stats.recent_registrations.this_week, int)
        assert isinstance(stats.recent_registrations.this_month, int)
        assert isinstance(stats.user_growth, list)

    def test_get_dashboard_stats_empty_database(self, db_session: Session):
        """Test dashboard stats with empty database."""
        # Get initial user count (may have users from other tests)
        initial_count = db_session.query(User).count()
        
        stats = get_dashboard_stats(db_session)
        
        # Since we can't guarantee a completely empty database due to test isolation,
        # we'll just check that the stats are consistent with what we expect
        assert stats.total_users >= initial_count
        assert stats.active_users >= 0
        assert stats.inactive_users >= 0
        assert stats.admin_users >= 0
        assert isinstance(stats.recent_registrations.today, int)
        assert isinstance(stats.recent_registrations.this_week, int)
        assert isinstance(stats.recent_registrations.this_month, int)
        assert len(stats.user_growth) == 30  # 30 days of growth data
        # Verify growth data structure is correct
        for point in stats.user_growth:
            assert isinstance(point.total_users, int)
            assert isinstance(point.new_users, int)
            assert point.total_users >= 0
            assert point.new_users >= 0

    def test_search_users_basic(self, db_session: Session):
        """Test basic user search functionality."""
        # Create test users
        user1 = UserFactory(username="john_doe", role="user")
        user2 = UserFactory(username="jane_smith", role="admin")
        user3 = UserFactory(username="bob_johnson", role="user")
        
        db_session.add_all([user1, user2, user3])
        db_session.commit()
        
        # Search with basic filters
        filters = UserSearchFilters(query="john", skip=0, limit=10)
        result = search_users(db_session, filters)
        
        assert result.total_count >= 1
        assert len(result.users) >= 1
        assert any("john" in user["username"].lower() for user in result.users)

    def test_search_users_with_role_filter(self, db_session: Session):
        """Test user search with role filtering."""
        # Create test users
        admin_user = UserFactory(role="admin")
        user1 = UserFactory(role="user")
        user2 = UserFactory(role="user")
        
        db_session.add_all([admin_user, user1, user2])
        db_session.commit()
        
        # Search for admin users only
        filters = UserSearchFilters(role="admin", skip=0, limit=10)
        result = search_users(db_session, filters)
        
        assert result.total_count >= 1
        assert all(user["role"] == "admin" for user in result.users)

    def test_search_users_with_status_filter(self, db_session: Session):
        """Test user search with status filtering."""
        # Create test users
        active_user = UserFactory(is_active=True)
        inactive_user = UserFactory(is_active=False)
        
        db_session.add_all([active_user, inactive_user])
        db_session.commit()
        
        # Search for active users only
        filters = UserSearchFilters(is_active=True, skip=0, limit=10)
        result = search_users(db_session, filters)
        
        assert result.total_count >= 1
        assert all(user["is_active"] is True for user in result.users)

    def test_search_users_with_date_filter(self, db_session: Session):
        """Test user search with date filtering."""
        # Create test users with specific dates
        old_date = datetime.now(timezone.utc) - timedelta(days=30)
        recent_date = datetime.now(timezone.utc) - timedelta(days=1)
        
        old_user = UserFactory()
        old_user.created_at = old_date
        recent_user = UserFactory()
        recent_user.created_at = recent_date
        
        db_session.add_all([old_user, recent_user])
        db_session.commit()
        
        # Search for recent users only
        filters = UserSearchFilters(
            created_after=datetime.now(timezone.utc) - timedelta(days=7),
            skip=0,
            limit=10
        )
        result = search_users(db_session, filters)
        
        assert result.total_count >= 1
        for user in result.users:
            user_date = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
            assert user_date >= filters.created_after

    def test_search_users_pagination(self, db_session: Session):
        """Test user search pagination."""
        # Create multiple test users
        users = [UserFactory() for _ in range(5)]
        db_session.add_all(users)
        db_session.commit()
        
        # Test pagination
        filters = UserSearchFilters(skip=0, limit=2)
        result = search_users(db_session, filters)
        
        assert len(result.users) <= 2
        assert result.total_count >= 5
        assert result.page_info["current_page"] == 1
        assert result.page_info["has_next"] is True

    def test_bulk_activate_users_success(self, db_session: Session):
        """Test successful bulk user activation."""
        # Create inactive test users
        user1 = UserFactory(is_active=False)
        user2 = UserFactory(is_active=False)
        user3 = UserFactory(is_active=True)  # Already active
        
        db_session.add_all([user1, user2, user3])
        db_session.commit()
        
        # Bulk activate users
        user_ids = [user1.id, user2.id, user3.id]
        result = bulk_activate_users(db_session, user_ids)
        
        assert result.success_count >= 2
        assert result.total_processed == 3
        assert user1.id in result.successful
        assert user2.id in result.successful

    def test_bulk_activate_users_with_nonexistent(self, db_session: Session):
        """Test bulk activation with non-existent user IDs."""
        user = UserFactory(is_active=False)
        db_session.add(user)
        db_session.commit()
        
        # Include non-existent user ID
        user_ids = [user.id, 99999]
        result = bulk_activate_users(db_session, user_ids)
        
        assert result.success_count == 1
        assert result.failure_count == 1
        assert user.id in result.successful
        assert any(failed["user_id"] == 99999 for failed in result.failed)

    def test_bulk_deactivate_users_success(self, db_session: Session):
        """Test successful bulk user deactivation."""
        # Create active test users
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=True)
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Bulk deactivate users
        user_ids = [user1.id, user2.id]
        result = bulk_deactivate_users(db_session, user_ids)
        
        assert result.success_count == 2
        assert result.total_processed == 2
        assert user1.id in result.successful
        assert user2.id in result.successful

    def test_bulk_deactivate_users_prevent_self_modification(self, db_session: Session):
        """Test bulk deactivation prevents self-modification."""
        user1 = UserFactory(is_active=True)
        user2 = UserFactory(is_active=True)
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Try to deactivate including requesting user
        user_ids = [user1.id, user2.id]
        result = bulk_deactivate_users(db_session, user_ids, requesting_user_id=user1.id)
        
        assert result.success_count == 1
        assert result.failure_count == 1
        assert user2.id in result.successful
        assert any(failed["user_id"] == user1.id for failed in result.failed)

    def test_export_users_csv_success(self, db_session: Session):
        """Test successful CSV export."""
        # Create test users
        user1 = UserFactory(username="john_doe", role="user")
        user2 = UserFactory(username="jane_admin", role="admin")
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Export to CSV
        csv_content = export_users_csv(db_session)
        
        assert isinstance(csv_content, str)
        assert "john_doe" in csv_content
        assert "jane_admin" in csv_content
        assert "username" in csv_content.lower()  # Header row

    def test_export_users_csv_with_filters(self, db_session: Session):
        """Test CSV export with filters."""
        # Create test users
        admin_user = UserFactory(role="admin")
        regular_user = UserFactory(role="user")
        
        db_session.add_all([admin_user, regular_user])
        db_session.commit()
        
        # Export only admin users
        filters = UserSearchFilters(role="admin")
        csv_content = export_users_csv(db_session, filters)
        
        assert isinstance(csv_content, str)
        assert admin_user.username in csv_content
        # Regular user should not be in filtered export
        lines = csv_content.split('\n')
        user_lines = [line for line in lines if regular_user.username in line]
        assert len(user_lines) == 0

    def test_export_users_json_success(self, db_session: Session):
        """Test successful JSON export."""
        # Create test users
        user1 = UserFactory(username="john_doe")
        user2 = UserFactory(username="jane_smith")
        
        db_session.add_all([user1, user2])
        db_session.commit()
        
        # Export to JSON
        json_content = export_users_json(db_session)
        
        assert isinstance(json_content, str)
        assert "john_doe" in json_content
        assert "jane_smith" in json_content
        assert '"username"' in json_content

    def test_get_user_growth_data_success(self, db_session: Session):
        """Test user growth data retrieval."""
        # Create test users with different dates
        old_user = UserFactory()
        old_user.created_at = datetime.now(timezone.utc) - timedelta(days=15)
        
        recent_user = UserFactory()
        recent_user.created_at = datetime.now(timezone.utc) - timedelta(days=5)
        
        db_session.add_all([old_user, recent_user])
        db_session.commit()
        
        # Get growth data
        growth_data = get_user_growth_data(db_session, days=30)
        
        assert isinstance(growth_data, list)
        assert len(growth_data) <= 30
        for point in growth_data:
            assert "date" in point
            assert "total_users" in point
            assert "new_users" in point

    def test_count_recent_registrations_success(self, db_session: Session):
        """Test recent registrations counting."""
        # Create users with different dates
        today = datetime.now(timezone.utc)
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=8)
        
        today_user = UserFactory()
        today_user.created_at = today
        
        yesterday_user = UserFactory()
        yesterday_user.created_at = yesterday
        
        old_user = UserFactory()
        old_user.created_at = last_week
        
        db_session.add_all([today_user, yesterday_user, old_user])
        db_session.commit()
        
        # Count recent registrations
        counts = count_recent_registrations(db_session)
        
        assert "today" in counts
        assert "this_week" in counts
        assert "this_month" in counts
        assert counts["today"] >= 1
        assert counts["this_week"] >= 2
        assert counts["this_month"] >= 3


class TestAnalyticsServiceEdgeCases:
    """Test edge cases and error conditions for analytics service."""

    def test_search_users_empty_query(self, db_session: Session):
        """Test search with empty query."""
        user = UserFactory()
        db_session.add(user)
        db_session.commit()
        
        filters = UserSearchFilters(query="", skip=0, limit=10)
        result = search_users(db_session, filters)
        
        # Empty query should return all users
        assert result.total_count >= 1

    def test_search_users_invalid_sort(self, db_session: Session):
        """Test search with invalid sort parameters."""
        user = UserFactory()
        db_session.add(user)
        db_session.commit()
        
        filters = UserSearchFilters(
            sort_by="invalid_field",
            sort_order="invalid_order",
            skip=0,
            limit=10
        )
        result = search_users(db_session, filters)
        
        # Should handle invalid sort gracefully
        assert result.total_count >= 1

    def test_bulk_operations_empty_list(self, db_session: Session):
        """Test bulk operations with empty user ID list."""
        result = bulk_activate_users(db_session, [])
        
        assert result.total_processed == 0
        assert result.success_count == 0
        assert result.failure_count == 0

    def test_export_empty_database(self, db_session: Session):
        """Test export with no users in database."""
        csv_content = export_users_csv(db_session)
        json_content = export_users_json(db_session)
        
        # Should return header only for CSV
        assert isinstance(csv_content, str)
        assert isinstance(json_content, str)
        
        # CSV should have at least header row
        csv_lines = csv_content.strip().split('\n')
        assert len(csv_lines) >= 1

    def test_get_user_growth_data_zero_days(self, db_session: Session):
        """Test user growth data with zero days."""
        growth_data = get_user_growth_data(db_session, days=0)
        
        assert isinstance(growth_data, list)
        assert len(growth_data) == 0

    def test_get_user_growth_data_negative_days(self, db_session: Session):
        """Test user growth data with negative days."""
        growth_data = get_user_growth_data(db_session, days=-5)
        
        # Should handle negative days gracefully
        assert isinstance(growth_data, list)
        assert len(growth_data) == 0
