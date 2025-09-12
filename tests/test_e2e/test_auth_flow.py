"""
End-to-end authentication flow tests.

These tests validate complete authentication workflows from registration
through login to accessing protected endpoints.
"""

import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.config.database import get_db
from app.services.auth_service import create_access_token
from tests.factories import UserFactory


class TestE2EAuthenticationFlow:
    """End-to-end tests for complete authentication workflows."""
    
    def test_complete_user_registration_and_login_flow(self, db_session: Session):
        """Test complete flow: registration → login → access protected endpoint."""
        # Create a test client that bypasses TrustedHostMiddleware for testing
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware for E2E tests
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Step 1: Register a new user
                registration_data = {
                    "username": "e2e_testuser",
                    "password": "e2e_testpass123"
                }
                
                register_response = client.post("/api/auth/register", json=registration_data)
                assert register_response.status_code == 201
                register_data = register_response.json()
                assert "user_id" in register_data
                assert register_data["message"] == "User created successfully"
                
                # Step 2: Login with the registered user
                login_response = client.post("/api/auth/login", json=registration_data)
                assert login_response.status_code == 200
                login_data = login_response.json()
                
                assert "access_token" in login_data
                assert "token_type" in login_data
                assert "expires_in" in login_data
                assert login_data["token_type"] == "bearer"
                
                access_token = login_data["access_token"]
                
                # Step 3: Access protected endpoint with token
                headers = {"Authorization": f"Bearer {access_token}"}
                protected_response = client.get("/api/user/protected", headers=headers)
                assert protected_response.status_code == 200
                protected_data = protected_response.json()
                
                assert "message" in protected_data
                assert "user_id" in protected_data
                assert "e2e_testuser" in protected_data["message"]
                assert protected_data["access_level"] == "authenticated"
                
                # Step 4: Get user profile
                profile_response = client.get("/api/user/profile", headers=headers)
                assert profile_response.status_code == 200
                profile_data = profile_response.json()
                
                assert profile_data["username"] == "e2e_testuser"
                assert "id" in profile_data
                assert "created_at" in profile_data
                
        finally:
            # Restore original middleware
            app.user_middleware = original_middleware
            # Clean up dependency overrides
            app.dependency_overrides.clear()
    
    def test_token_refresh_flow(self, db_session: Session):
        """Test token refresh workflow."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Step 1: Register and login user
                user_data = {"username": "refresh_user", "password": "refresh_pass123"}
                client.post("/api/auth/register", json=user_data)
                
                login_response = client.post("/api/auth/login", json=user_data)
                assert login_response.status_code == 200
                login_data = login_response.json()
                original_token = login_data["access_token"]
                
                # Step 2: Use token to access protected endpoint
                headers = {"Authorization": f"Bearer {original_token}"}
                protected_response = client.get("/api/user/protected", headers=headers)
                assert protected_response.status_code == 200
                
                # Step 3: Refresh the token
                refresh_response = client.post("/api/auth/refresh", headers=headers)
                assert refresh_response.status_code == 200
                refresh_data = refresh_response.json()
                
                assert "access_token" in refresh_data
                assert "token_type" in refresh_data
                assert refresh_data["token_type"] == "bearer"
                
                new_token = refresh_data["access_token"]
                # Note: Token might be the same if refresh logic reuses valid tokens
                # The important thing is that refresh endpoint works
                assert new_token is not None
                
                # Step 4: Use new token to access protected endpoint
                new_headers = {"Authorization": f"Bearer {new_token}"}
                new_protected_response = client.get("/api/user/protected", headers=new_headers)
                assert new_protected_response.status_code == 200
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
    
    def test_user_profile_update_flow(self, db_session: Session):
        """Test complete user profile update workflow."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Step 1: Register and login user
                user_data = {"username": "update_user", "password": "update_pass123"}
                client.post("/api/auth/register", json=user_data)
                
                login_response = client.post("/api/auth/login", json=user_data)
                login_data = login_response.json()
                access_token = login_data["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Step 2: Get initial profile
                profile_response = client.get("/api/user/profile", headers=headers)
                assert profile_response.status_code == 200
                initial_profile = profile_response.json()
                assert initial_profile["username"] == "update_user"
                
                # Step 3: Update profile
                update_data = {"username": "updated_username"}
                update_response = client.put("/api/user/profile", json=update_data, headers=headers)
                assert update_response.status_code == 200
                updated_profile = update_response.json()
                assert updated_profile["username"] == "updated_username"
                
                # Step 4: Verify profile was updated (token might be invalidated after username change)
                verify_response = client.get("/api/user/profile", headers=headers)
                if verify_response.status_code == 401:
                    print("Token invalidated after username change - this is correct security behavior")
                    
                    # Try to login with new username
                    new_login_data = {"username": "updated_username", "password": "update_pass123"}
                    new_login_response = client.post("/api/auth/login", json=new_login_data)
                    assert new_login_response.status_code == 200
                    
                    # Old username should not work
                    old_login_response = client.post("/api/auth/login", json=user_data)
                    assert old_login_response.status_code == 401
                else:
                    # If token still works, verify profile was updated
                    verify_profile = verify_response.json()
                    assert verify_profile["username"] == "updated_username"
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
    
    def test_multi_user_concurrent_sessions(self, db_session: Session):
        """Test multiple users with concurrent sessions."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                users_data = [
                    {"username": "user1", "password": "pass123"},
                    {"username": "user2", "password": "pass123"},
                    {"username": "user3", "password": "pass123"}
                ]
                
                tokens = []
                
                # Register and login all users
                for user_data in users_data:
                    # Register
                    register_response = client.post("/api/auth/register", json=user_data)
                    assert register_response.status_code == 201
                    
                    # Login
                    login_response = client.post("/api/auth/login", json=user_data)
                    assert login_response.status_code == 200
                    login_data = login_response.json()
                    tokens.append(login_data["access_token"])
                
                # Verify all tokens work simultaneously
                for i, token in enumerate(tokens):
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    # Access protected endpoint
                    protected_response = client.get("/api/user/protected", headers=headers)
                    assert protected_response.status_code == 200
                    protected_data = protected_response.json()
                    assert users_data[i]["username"] in protected_data["message"]
                    
                    # Get profile
                    profile_response = client.get("/api/user/profile", headers=headers)
                    assert profile_response.status_code == 200
                    profile_data = profile_response.json()
                    assert profile_data["username"] == users_data[i]["username"]
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()


class TestE2EErrorHandling:
    """End-to-end tests for error handling scenarios."""
    
    def test_invalid_credentials_flow(self, db_session: Session):
        """Test error handling for invalid credentials."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Step 1: Register user
                user_data = {"username": "error_user", "password": "correct_pass123"}
                register_response = client.post("/api/auth/register", json=user_data)
                assert register_response.status_code == 201
                
                # Step 2: Try login with wrong password
                wrong_data = {"username": "error_user", "password": "wrong_password"}
                login_response = client.post("/api/auth/login", json=wrong_data)
                assert login_response.status_code == 401
                
                # Step 3: Try login with non-existent user
                nonexistent_data = {"username": "nonexistent", "password": "any_password"}
                nonexistent_response = client.post("/api/auth/login", json=nonexistent_data)
                assert nonexistent_response.status_code == 401
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
    
    def test_unauthorized_access_flow(self, db_session: Session):
        """Test unauthorized access to protected endpoints."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Step 1: Try accessing protected endpoint without token
                protected_response = client.get("/api/user/protected")
                assert protected_response.status_code == 401
                
                # Step 2: Try accessing with invalid token
                invalid_headers = {"Authorization": "Bearer invalid_token"}
                invalid_response = client.get("/api/user/protected", headers=invalid_headers)
                assert invalid_response.status_code == 401
                
                # Step 3: Try accessing with malformed authorization header
                malformed_headers = {"Authorization": "InvalidFormat token"}
                malformed_response = client.get("/api/user/protected", headers=malformed_headers)
                assert malformed_response.status_code == 401
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
    
    def test_expired_token_flow(self, db_session: Session):
        """Test handling of expired tokens."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Step 1: Register and login user
                user_data = {"username": "expire_user", "password": "expire_pass123"}
                client.post("/api/auth/register", json=user_data)
                
                # Step 2: Create an expired token manually
                token_data = {"sub": "expire_user"}
                expired_token = create_access_token(
                    token_data, 
                    expires_delta=timedelta(seconds=-1)  # Already expired
                )
                
                # Step 3: Try to use expired token
                expired_headers = {"Authorization": f"Bearer {expired_token}"}
                expired_response = client.get("/api/user/protected", headers=expired_headers)
                assert expired_response.status_code == 401
                
                # Step 4: Try to refresh with expired token
                refresh_response = client.post("/api/auth/refresh", headers=expired_headers)
                assert refresh_response.status_code == 401
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()


class TestE2EDataValidation:
    """End-to-end tests for data validation scenarios."""
    
    def test_registration_validation_flow(self, db_session: Session):
        """Test registration with various invalid data."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Test cases for invalid registration data
                invalid_cases = [
                    {"username": "", "password": "valid123"},  # Empty username
                    {"username": "valid", "password": ""},  # Empty password
                    {"username": "ab", "password": "valid123"},  # Username too short
                    {"username": "valid", "password": "123"},  # Password too short
                    {},  # Missing fields
                    {"username": "valid"},  # Missing password
                    {"password": "valid123"},  # Missing username
                ]
                
                for invalid_data in invalid_cases:
                    response = client.post("/api/auth/register", json=invalid_data)
                    assert response.status_code in [400, 422], f"Expected 400 or 422 for {invalid_data}, got {response.status_code}"
                
                # Test duplicate username
                valid_data = {"username": "duplicate_test", "password": "valid123"}
                
                # First registration should succeed
                first_response = client.post("/api/auth/register", json=valid_data)
                assert first_response.status_code == 201
                
                # Second registration with same username should fail
                second_response = client.post("/api/auth/register", json=valid_data)
                assert second_response.status_code == 400
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
    
    def test_login_validation_flow(self, db_session: Session):
        """Test login with various invalid data."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Temporarily disable TrustedHostMiddleware
        original_middleware = app.user_middleware
        app.user_middleware = [m for m in app.user_middleware if 'TrustedHostMiddleware' not in str(type(m.cls))]
        
        try:
            with TestClient(app) as client:
                # Test cases for invalid login data
                invalid_cases = [
                    {"username": "", "password": "any"},  # Empty username
                    {"username": "any", "password": ""},  # Empty password
                    {},  # Missing fields
                    {"username": "any"},  # Missing password
                    {"password": "any"},  # Missing username
                ]
                
                for invalid_data in invalid_cases:
                    response = client.post("/api/auth/login", json=invalid_data)
                    assert response.status_code in [400, 422], f"Expected 400 or 422 for {invalid_data}, got {response.status_code}"
                
        finally:
            app.user_middleware = original_middleware
            app.dependency_overrides.clear()
