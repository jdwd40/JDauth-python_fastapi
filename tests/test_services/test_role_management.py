"""
Test module for role management functionality using TDD approach.

This module tests the enhanced role management system including:
- User role assignments
- User status management (active/inactive)
- Role-based authentication
- Safety checks for admin operations
"""

import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services import user_service
from tests.factories import UserFactory, create_user_in_db


class TestUserRoleManagement:
    """Test cases for user role management functionality."""

    def test_create_user_with_default_role_and_status(self, db_session: Session):
        """Test that new users are created with default role 'user' and active status."""
        user_data = UserCreate(username="newuser", password="password123")
        
        user = user_service.create_user(db_session, user_data)
        
        assert user.role == "user"
        assert user.is_active is True

    def test_create_admin_user(self, db_session: Session):
        """Test creating a user with admin role."""
        user_data = UserCreate(username="adminuser", password="password123")
        
        user = user_service.create_user_with_role(db_session, user_data, role="admin")
        
        assert user.role == "admin"
        assert user.is_active is True

    def test_assign_admin_role_to_user(self, db_session: Session):
        """Test assigning admin role to an existing user."""
        # Create regular user
        user = create_user_in_db(db_session, username="regularuser")
        assert user.role == "user"
        
        # Assign admin role
        updated_user = user_service.assign_user_role(db_session, user.id, "admin")
        
        assert updated_user.role == "admin"
        assert updated_user.is_active is True

    def test_assign_user_role_to_admin(self, db_session: Session):
        """Test demoting admin to regular user role."""
        # Create admin user
        user = create_user_in_db(db_session, username="adminuser", role="admin")
        assert user.role == "admin"
        
        # Demote to user role
        updated_user = user_service.assign_user_role(db_session, user.id, "user")
        
        assert updated_user.role == "user"

    def test_assign_invalid_role_raises_error(self, db_session: Session):
        """Test that assigning invalid role raises ValueError."""
        user = create_user_in_db(db_session, username="testuser")
        
        with pytest.raises(ValueError, match="Invalid role"):
            user_service.assign_user_role(db_session, user.id, "superadmin")

    def test_assign_role_to_nonexistent_user_raises_error(self, db_session: Session):
        """Test that assigning role to non-existent user raises ValueError."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.assign_user_role(db_session, 99999, "admin")

    def test_deactivate_user(self, db_session: Session):
        """Test deactivating a user."""
        user = create_user_in_db(db_session, username="activeuser")
        assert user.is_active is True
        
        updated_user = user_service.set_user_status(db_session, user.id, is_active=False)
        
        assert updated_user.is_active is False

    def test_activate_user(self, db_session: Session):
        """Test activating a deactivated user."""
        user = create_user_in_db(db_session, username="inactiveuser", is_active=False)
        assert user.is_active is False
        
        updated_user = user_service.set_user_status(db_session, user.id, is_active=True)
        
        assert updated_user.is_active is True

    def test_set_status_for_nonexistent_user_raises_error(self, db_session: Session):
        """Test that setting status for non-existent user raises ValueError."""
        with pytest.raises(ValueError, match="User not found"):
            user_service.set_user_status(db_session, 99999, is_active=False)

    def test_prevent_admin_self_demotion(self, db_session: Session):
        """Test that admin users cannot demote themselves."""
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        
        with pytest.raises(ValueError, match="Cannot modify your own role"):
            user_service.assign_user_role(
                db_session, 
                admin_user.id, 
                "user", 
                requesting_user_id=admin_user.id
            )

    def test_prevent_admin_self_deactivation(self, db_session: Session):
        """Test that admin users cannot deactivate themselves."""
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        
        with pytest.raises(ValueError, match="Cannot modify your own status"):
            user_service.set_user_status(
                db_session, 
                admin_user.id, 
                is_active=False, 
                requesting_user_id=admin_user.id
            )

    def test_admin_can_modify_other_users_role(self, db_session: Session):
        """Test that admin can modify other users' roles."""
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        regular_user = create_user_in_db(db_session, username="user")
        
        updated_user = user_service.assign_user_role(
            db_session, 
            regular_user.id, 
            "admin", 
            requesting_user_id=admin_user.id
        )
        
        assert updated_user.role == "admin"

    def test_admin_can_modify_other_users_status(self, db_session: Session):
        """Test that admin can modify other users' status."""
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        regular_user = create_user_in_db(db_session, username="user")
        
        updated_user = user_service.set_user_status(
            db_session, 
            regular_user.id, 
            is_active=False, 
            requesting_user_id=admin_user.id
        )
        
        assert updated_user.is_active is False

    def test_get_users_by_role(self, db_session: Session):
        """Test filtering users by role."""
        # Create users with different roles
        user1 = create_user_in_db(db_session, username="user1", role="user")
        user2 = create_user_in_db(db_session, username="user2", role="user")
        admin1 = create_user_in_db(db_session, username="admin1", role="admin")
        
        # Get only admin users
        admin_users = user_service.get_users_by_role(db_session, role="admin")
        admin_usernames = [user.username for user in admin_users]
        assert "admin1" in admin_usernames
        
        # Get only regular users
        regular_users = user_service.get_users_by_role(db_session, role="user")
        regular_usernames = [user.username for user in regular_users]
        assert "user1" in regular_usernames
        assert "user2" in regular_usernames
        # Verify our created users are in the results (may be more from other tests)
        assert len([u for u in regular_users if u.username in ["user1", "user2"]]) == 2

    def test_get_users_by_status(self, db_session: Session):
        """Test filtering users by active status."""
        # Create users with different statuses
        active1 = create_user_in_db(db_session, username="active1", is_active=True)
        active2 = create_user_in_db(db_session, username="active2", is_active=True)
        inactive1 = create_user_in_db(db_session, username="inactive1", is_active=False)
        
        # Get only active users
        active_users = user_service.get_users_by_status(db_session, is_active=True)
        active_usernames = [user.username for user in active_users]
        assert "active1" in active_usernames
        assert "active2" in active_usernames
        # Verify our created users are in the results (may be more from other tests)
        assert len([u for u in active_users if u.username in ["active1", "active2"]]) == 2
        
        # Get only inactive users
        inactive_users = user_service.get_users_by_status(db_session, is_active=False)
        inactive_usernames = [user.username for user in inactive_users]
        assert "inactive1" in inactive_usernames

    def test_count_users_by_role(self, db_session: Session):
        """Test counting users by role."""
        # Get baseline counts
        initial_user_count = user_service.count_users_by_role(db_session, "user")
        initial_admin_count = user_service.count_users_by_role(db_session, "admin")
        
        # Create users with different roles
        create_user_in_db(db_session, username="user1", role="user")
        create_user_in_db(db_session, username="user2", role="user")
        create_user_in_db(db_session, username="admin1", role="admin")
        create_user_in_db(db_session, username="admin2", role="admin")
        
        # Check that counts increased by the expected amount
        final_user_count = user_service.count_users_by_role(db_session, "user")
        final_admin_count = user_service.count_users_by_role(db_session, "admin")
        
        assert final_user_count == initial_user_count + 2
        assert final_admin_count == initial_admin_count + 2

    def test_count_users_by_status(self, db_session: Session):
        """Test counting users by active status."""
        # Get baseline counts
        initial_active_count = user_service.count_users_by_status(db_session, is_active=True)
        initial_inactive_count = user_service.count_users_by_status(db_session, is_active=False)
        
        # Create users with different statuses
        create_user_in_db(db_session, username="active1", is_active=True)
        create_user_in_db(db_session, username="active2", is_active=True)
        create_user_in_db(db_session, username="inactive1", is_active=False)
        
        # Check that counts increased by the expected amount
        final_active_count = user_service.count_users_by_status(db_session, is_active=True)
        final_inactive_count = user_service.count_users_by_status(db_session, is_active=False)
        
        assert final_active_count == initial_active_count + 2
        assert final_inactive_count == initial_inactive_count + 1


class TestAuthenticationWithRoles:
    """Test cases for authentication system with role-based access."""

    def test_is_admin_user_with_role_field(self, db_session: Session):
        """Test admin detection using role field."""
        from app.controllers.user_controller import UserController
        
        controller = UserController()
        
        # Test admin user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        assert controller._is_admin_user(admin_user) is True
        
        # Test regular user
        regular_user = create_user_in_db(db_session, username="user", role="user")
        assert controller._is_admin_user(regular_user) is False

    def test_is_admin_user_inactive_admin(self, db_session: Session):
        """Test that inactive admin users are not considered admin."""
        from app.controllers.user_controller import UserController
        
        controller = UserController()
        
        # Test inactive admin user
        inactive_admin = create_user_in_db(
            db_session, 
            username="inactiveadmin", 
            role="admin", 
            is_active=False
        )
        assert controller._is_admin_user(inactive_admin) is False

    def test_require_admin_dependency_with_role_field(self, db_session: Session):
        """Test require_admin dependency using role field."""
        from app.utils.dependencies import require_admin
        
        # Test with admin user
        admin_user = create_user_in_db(db_session, username="admin", role="admin")
        result = require_admin(current_user=admin_user)
        assert result == admin_user
        
        # Test with regular user - should raise HTTPException
        regular_user = create_user_in_db(db_session, username="user", role="user")
        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=regular_user)
        assert exc_info.value.status_code == 403

    def test_require_admin_dependency_with_inactive_admin(self, db_session: Session):
        """Test require_admin dependency with inactive admin user."""
        from app.utils.dependencies import get_current_active_user
        
        # Test with inactive admin user - should raise HTTPException at get_current_active_user level
        inactive_admin = create_user_in_db(
            db_session, 
            username="inactiveadmin", 
            role="admin", 
            is_active=False
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(current_user=inactive_admin)
        assert exc_info.value.status_code == 400

    def test_get_current_active_user_with_inactive_user(self, db_session: Session):
        """Test get_current_active_user dependency with inactive user."""
        from app.utils.dependencies import get_current_active_user
        
        # Test with inactive user - should raise HTTPException
        inactive_user = create_user_in_db(
            db_session, 
            username="inactiveuser", 
            is_active=False
        )
        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(current_user=inactive_user)
        assert exc_info.value.status_code == 400
        assert "Inactive user" in str(exc_info.value.detail)
