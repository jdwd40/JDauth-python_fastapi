"""
Integration tests for service layer interactions.
"""

import pytest
from datetime import timedelta
from sqlalchemy.orm import Session

from app.services.user_service import (
    create_user,
    get_user_by_username,
    get_user_by_id,
    update_user,
    delete_user
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    verify_token,
    get_current_user_from_token
)
from app.schemas.user import UserCreate, UserUpdate
from tests.factories import UserCreateFactory, UserUpdateFactory


class TestUserAuthServiceIntegration:
    """Test integration between user service and auth service."""
    
    @pytest.mark.integration
    def test_create_user_and_authenticate(self, db_session: Session):
        """Test creating a user and then authenticating them."""
        # Arrange
        user_data = UserCreateFactory(username="integrationuser", password="password123")
        
        # Act 1: Create user
        created_user = create_user(db_session, user_data)
        assert created_user is not None
        
        # Act 2: Authenticate user
        authenticated_user = authenticate_user(db_session, user_data.username, user_data.password)
        
        # Assert
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        assert authenticated_user.username == created_user.username
    
    @pytest.mark.integration
    def test_user_update_affects_authentication(self, db_session: Session):
        """Test that updating user password affects authentication."""
        # Arrange
        original_password = "originalpassword123"
        new_password = "newpassword123"
        user_data = UserCreateFactory(username="updateuser", password=original_password)
        
        # Act 1: Create user
        created_user = create_user(db_session, user_data)
        
        # Act 2: Verify original authentication works
        auth_result = authenticate_user(db_session, user_data.username, original_password)
        assert auth_result is not None
        
        # Act 3: Update password
        update_data = UserUpdate(password=new_password)
        updated_user = update_user(db_session, created_user.id, update_data)
        
        # Act 4: Test authentication with old password fails
        old_auth = authenticate_user(db_session, user_data.username, original_password)
        assert old_auth is None
        
        # Act 5: Test authentication with new password works
        new_auth = authenticate_user(db_session, user_data.username, new_password)
        assert new_auth is not None
        assert new_auth.id == created_user.id
    
    @pytest.mark.integration
    def test_deleted_user_cannot_authenticate(self, db_session: Session):
        """Test that deleted users cannot authenticate."""
        # Arrange
        user_data = UserCreateFactory(username="deleteuser", password="password123")
        
        # Act 1: Create user
        created_user = create_user(db_session, user_data)
        
        # Act 2: Verify authentication works
        auth_result = authenticate_user(db_session, user_data.username, user_data.password)
        assert auth_result is not None
        
        # Act 3: Delete user
        delete_result = delete_user(db_session, created_user.id)
        assert delete_result is True
        
        # Act 4: Verify authentication fails
        auth_after_delete = authenticate_user(db_session, user_data.username, user_data.password)
        assert auth_after_delete is None
    
    @pytest.mark.integration
    def test_complete_auth_workflow(self, db_session: Session):
        """Test complete authentication workflow from user creation to token usage."""
        # Arrange
        user_data = UserCreateFactory(username="workflowuser", password="workflow123")
        
        # Step 1: Create user
        created_user = create_user(db_session, user_data)
        assert created_user is not None
        
        # Step 2: Authenticate user
        authenticated_user = authenticate_user(db_session, user_data.username, user_data.password)
        assert authenticated_user is not None
        
        # Step 3: Create access token
        token_data = {"sub": authenticated_user.username}
        access_token = create_access_token(token_data, timedelta(minutes=30))
        assert access_token is not None
        
        # Step 4: Verify token
        payload = verify_token(access_token)
        assert payload["sub"] == authenticated_user.username
        
        # Step 5: Get user from token
        token_user = get_current_user_from_token(db_session, access_token)
        assert token_user.id == created_user.id
        assert token_user.username == created_user.username
    
    @pytest.mark.integration
    def test_token_survives_user_updates(self, db_session: Session):
        """Test that valid tokens remain valid after non-username user updates."""
        # Arrange
        user_data = UserCreateFactory(username="tokenuser", password="tokenpass123")
        
        # Step 1: Create user and get token
        created_user = create_user(db_session, user_data)
        authenticated_user = authenticate_user(db_session, user_data.username, user_data.password)
        token_data = {"sub": authenticated_user.username}
        access_token = create_access_token(token_data, timedelta(minutes=30))
        
        # Step 2: Verify token works
        token_user_before = get_current_user_from_token(db_session, access_token)
        assert token_user_before.id == created_user.id
        
        # Step 3: Update user password (not username)
        update_data = UserUpdate(password="newtokenpass123")
        updated_user = update_user(db_session, created_user.id, update_data)
        
        # Step 4: Verify token still works (username unchanged)
        token_user_after = get_current_user_from_token(db_session, access_token)
        assert token_user_after.id == created_user.id
        assert token_user_after.username == created_user.username
    
    @pytest.mark.integration
    def test_token_invalidated_by_username_change(self, db_session: Session):
        """Test that tokens become invalid when username changes."""
        # Arrange
        original_username = "originaltoken"
        new_username = "newtoken"
        user_data = UserCreateFactory(username=original_username, password="tokenpass123")
        
        # Step 1: Create user and get token
        created_user = create_user(db_session, user_data)
        authenticated_user = authenticate_user(db_session, user_data.username, user_data.password)
        token_data = {"sub": authenticated_user.username}
        access_token = create_access_token(token_data, timedelta(minutes=30))
        
        # Step 2: Verify token works
        token_user_before = get_current_user_from_token(db_session, access_token)
        assert token_user_before.username == original_username
        
        # Step 3: Update username
        update_data = UserUpdate(username=new_username)
        updated_user = update_user(db_session, created_user.id, update_data)
        
        # Step 4: Verify token no longer works (username changed)
        with pytest.raises(ValueError, match="User not found"):
            get_current_user_from_token(db_session, access_token)
    
    @pytest.mark.integration
    def test_token_invalidated_by_user_deletion(self, db_session: Session):
        """Test that tokens become invalid when user is deleted."""
        # Arrange
        user_data = UserCreateFactory(username="deletedtoken", password="tokenpass123")
        
        # Step 1: Create user and get token
        created_user = create_user(db_session, user_data)
        authenticated_user = authenticate_user(db_session, user_data.username, user_data.password)
        token_data = {"sub": authenticated_user.username}
        access_token = create_access_token(token_data, timedelta(minutes=30))
        
        # Step 2: Verify token works
        token_user_before = get_current_user_from_token(db_session, access_token)
        assert token_user_before.id == created_user.id
        
        # Step 3: Delete user
        delete_result = delete_user(db_session, created_user.id)
        assert delete_result is True
        
        # Step 4: Verify token no longer works (user deleted)
        with pytest.raises(ValueError, match="User not found"):
            get_current_user_from_token(db_session, access_token)


class TestErrorHandlingIntegration:
    """Test error handling across service integrations."""
    
    @pytest.mark.integration
    def test_authenticate_nonexistent_user_for_token(self, db_session: Session):
        """Test error handling when trying to create token for nonexistent user."""
        # Act & Assert
        auth_result = authenticate_user(db_session, "nonexistent", "password")
        assert auth_result is None
    
    @pytest.mark.integration
    def test_token_for_invalid_user_data(self, db_session: Session):
        """Test token creation with invalid user data."""
        # Arrange
        invalid_token_data = {"sub": ""}  # Empty username
        
        # Act
        token = create_access_token(invalid_token_data, timedelta(minutes=30))
        
        # Assert - Token creation succeeds but user lookup fails
        with pytest.raises(ValueError, match="Invalid token payload"):
            get_current_user_from_token(db_session, token)
    
    @pytest.mark.integration
    def test_concurrent_user_operations(self, db_session: Session):
        """Test that user operations work correctly in sequence."""
        # This simulates concurrent-like operations in sequence
        
        # Create multiple users
        users_data = [
            UserCreateFactory(username=f"concurrent{i}", password=f"password{i}123")
            for i in range(3)
        ]
        
        created_users = []
        tokens = []
        
        # Create users and tokens
        for user_data in users_data:
            user = create_user(db_session, user_data)
            created_users.append(user)
            
            auth_user = authenticate_user(db_session, user_data.username, user_data.password)
            token_data = {"sub": auth_user.username}
            token = create_access_token(token_data, timedelta(minutes=30))
            tokens.append(token)
        
        # Verify all tokens work
        for i, token in enumerate(tokens):
            token_user = get_current_user_from_token(db_session, token)
            assert token_user.id == created_users[i].id
            assert token_user.username == users_data[i].username
        
        # Update one user
        update_data = UserUpdate(username="updated_concurrent0")
        updated_user = update_user(db_session, created_users[0].id, update_data)
        
        # Verify first token no longer works, others still work
        with pytest.raises(ValueError, match="User not found"):
            get_current_user_from_token(db_session, tokens[0])
        
        for i in range(1, len(tokens)):
            token_user = get_current_user_from_token(db_session, tokens[i])
            assert token_user.id == created_users[i].id
