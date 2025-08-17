"""
Comprehensive tests for authentication functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.auth.authentication_service import authentication_service
from src.backend.auth import schemas, models


class TestAuthenticationService:
    """Test authentication service functionality."""

    def test_get_current_user_valid_token(self, client: TestClient, auth_headers, create_test_user):
        """Test getting current user with valid token."""
        response = client.get("/welcome", headers=auth_headers)
        assert response.status_code == 200
        assert "Welcome" in response.json()["msg"]

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/welcome", headers=headers)
        assert response.status_code == 403

    def test_get_current_user_no_token(self, client: TestClient):
        """Test accessing protected endpoint without token."""
        response = client.get("/welcome")
        assert response.status_code == 401

    def test_role_based_access_user(self, client: TestClient, auth_headers):
        """Test user role access to user endpoint."""
        response = client.get("/user/me", headers=auth_headers)
        assert response.status_code == 200
        assert "user-specific" in response.json()["msg"]

    def test_role_based_access_superuser_denied(self, client: TestClient, auth_headers):
        """Test user role denied access to superuser endpoint."""
        response = client.get("/superuser/me", headers=auth_headers)
        assert response.status_code == 403

    def test_role_based_access_admin_denied(self, client: TestClient, auth_headers):
        """Test user role denied access to admin endpoint."""
        response = client.get("/admin/me", headers=auth_headers)
        assert response.status_code == 403

    def test_admin_access_all_endpoints(self, client: TestClient, admin_headers):
        """Test admin can access all endpoints."""
        endpoints = ["/user/me", "/superuser/me", "/admin/me"]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=admin_headers)
            assert response.status_code == 200

    def test_verify_user_access_to_tenant(self, create_test_user):
        """Test tenant access verification."""
        # User should have access to their own tenant
        has_access = authentication_service.verify_user_access_to_tenant(
            create_test_user, create_test_user.tenant_name
        )
        assert has_access is True
        
        # User should not have access to different tenant
        has_access = authentication_service.verify_user_access_to_tenant(
            create_test_user, "different-tenant"
        )
        assert has_access is False

    def test_admin_access_all_tenants(self, create_test_admin):
        """Test admin has access to all tenants."""
        has_access = authentication_service.verify_user_access_to_tenant(
            create_test_admin, "any-tenant"
        )
        assert has_access is True


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    def test_signup_success(self, client: TestClient):
        """Test successful user signup."""
        user_data = {
            "email": "signup@example.com",
            "password": "signuppass123",
            "full_name": "Signup User",
            "tenant_name": "signup-tenant"
        }
        
        response = client.post("/api/v1/signup", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert data["tenant_name"] == user_data["tenant_name"]

    def test_signup_duplicate_email(self, client: TestClient, test_user_data, create_test_user):
        """Test signup with duplicate email."""
        response = client.post("/api/v1/signup", json=test_user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_signup_invalid_password(self, client: TestClient):
        """Test signup with invalid password."""
        user_data = {
            "email": "invalid@example.com",
            "password": "short",  # Too short
            "full_name": "Invalid User",
            "tenant_name": "invalid-tenant"
        }
        
        response = client.post("/api/v1/signup", json=user_data)
        assert response.status_code == 422  # Validation error

    def test_login_success(self, client: TestClient, test_user_data, create_test_user):
        """Test successful login."""
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user_data, create_test_user):
        """Test login with wrong password."""
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        assert response.status_code == 400

    def test_forgot_password(self, client: TestClient, create_test_user):
        """Test forgot password functionality."""
        response = client.post("/api/v1/forgot-password", json=create_test_user.email)
        assert response.status_code == 200
        assert "email sent" in response.json()["msg"]

    def test_change_password_success(self, client: TestClient, auth_headers, test_user_data):
        """Test successful password change."""
        password_data = {
            "current_password": test_user_data["password"],
            "new_password": "newpassword123"
        }
        
        response = client.post("/api/v1/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 200
        assert "successfully" in response.json()["msg"]

    def test_change_password_wrong_current(self, client: TestClient, auth_headers):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        
        response = client.post("/api/v1/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"]

    def test_change_password_unauthenticated(self, client: TestClient):
        """Test password change without authentication."""
        password_data = {
            "current_password": "password123",
            "new_password": "newpassword123"
        }
        
        response = client.post("/api/v1/change-password", json=password_data)
        assert response.status_code == 401


class TestMultiTenantAuthentication:
    """Test multi-tenant authentication features."""

    def test_user_isolation_by_tenant(self, client: TestClient, db_session: Session):
        """Test that users are properly isolated by tenant."""
        # Create users in different tenants
        tenant1_user_data = {
            "email": "tenant1@example.com",
            "password": "password123",
            "full_name": "Tenant 1 User",
            "tenant_name": "tenant-1"
        }
        
        tenant2_user_data = {
            "email": "tenant2@example.com",
            "password": "password123",
            "full_name": "Tenant 2 User",
            "tenant_name": "tenant-2"
        }
        
        # Create both users
        response1 = client.post("/api/v1/signup", json=tenant1_user_data)
        response2 = client.post("/api/v1/signup", json=tenant2_user_data)
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        user1_data = response1.json()
        user2_data = response2.json()
        
        # Verify they have different tenant names
        assert user1_data["tenant_name"] != user2_data["tenant_name"]

    def test_tenant_database_separation(self, client: TestClient):
        """Test that tenants have separate databases."""
        # This test would verify that chat messages and other tenant-specific
        # data are stored in separate databases
        # For now, we'll test the basic tenant creation
        
        user_data = {
            "email": "dbtest@example.com",
            "password": "password123",
            "full_name": "DB Test User",
            "tenant_name": "db-test-tenant"
        }
        
        response = client.post("/api/v1/signup", json=user_data)
        assert response.status_code == 201
        
        # Verify tenant-specific database would be created
        # (This would require checking the file system in a real test)
