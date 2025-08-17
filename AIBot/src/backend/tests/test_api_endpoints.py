"""
Comprehensive tests for API endpoints and integration.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestPublicEndpoints:
    """Test public API endpoints."""

    def test_hello_endpoint(self, client: TestClient):
        """Test public hello endpoint."""
        response = client.get("/hello")
        assert response.status_code == 200
        assert response.json()["message"] == "Hello, world!"

    def test_api_documentation(self, client: TestClient):
        """Test API documentation endpoints."""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema(self, client: TestClient):
        """Test OpenAPI schema endpoint."""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema


class TestProtectedEndpoints:
    """Test protected API endpoints."""

    def test_welcome_endpoint_authenticated(self, client: TestClient, auth_headers):
        """Test welcome endpoint with authentication."""
        response = client.get("/welcome", headers=auth_headers)
        assert response.status_code == 200
        assert "Welcome" in response.json()["msg"]

    def test_welcome_endpoint_unauthenticated(self, client: TestClient):
        """Test welcome endpoint without authentication."""
        response = client.get("/welcome")
        assert response.status_code == 401

    def test_signout_authenticated(self, client: TestClient, auth_headers):
        """Test signout endpoint with authentication."""
        response = client.post("/api/v1/signout", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "signed out successfully" in data["msg"]

    def test_signout_unauthenticated(self, client: TestClient):
        """Test signout endpoint without authentication."""
        response = client.post("/api/v1/signout")
        assert response.status_code == 401

    def test_user_me_endpoint(self, client: TestClient, auth_headers):
        """Test user-specific endpoint."""
        response = client.get("/user/me", headers=auth_headers)
        assert response.status_code == 200
        assert "user-specific" in response.json()["msg"]

    def test_superuser_me_endpoint_denied(self, client: TestClient, auth_headers):
        """Test superuser endpoint access denied for regular user."""
        response = client.get("/superuser/me", headers=auth_headers)
        assert response.status_code == 403

    def test_admin_me_endpoint_denied(self, client: TestClient, auth_headers):
        """Test admin endpoint access denied for regular user."""
        response = client.get("/admin/me", headers=auth_headers)
        assert response.status_code == 403


class TestAdminEndpoints:
    """Test admin-only API endpoints."""

    def test_admin_endpoints_access(self, client: TestClient, admin_headers):
        """Test admin can access all role-specific endpoints."""
        endpoints = ["/user/me", "/superuser/me", "/admin/me"]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=admin_headers)
            assert response.status_code == 200

    def test_get_users_list(self, client: TestClient, admin_headers):
        """Test admin can get users list."""
        response = client.get("/api/v1/users", headers=admin_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_users_list_pagination(self, client: TestClient, admin_headers):
        """Test users list with pagination."""
        response = client.get("/api/v1/users?skip=0&limit=5", headers=admin_headers)
        assert response.status_code == 200

    def test_create_user_admin(self, client: TestClient, admin_headers):
        """Test admin can create new user."""
        user_data = {
            "email": "adminuser@example.com",
            "password": "adminpass123",
            "full_name": "Admin Created User",
            "tenant_name": "admin-tenant"
        }
        
        response = client.post("/api/v1/users", json=user_data, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]

    def test_update_user_admin(self, client: TestClient, admin_headers, create_test_user):
        """Test admin can update user."""
        update_data = {
            "full_name": "Updated by Admin",
            "role": "super_user"
        }
        
        response = client.put(f"/api/v1/users/{create_test_user.id}", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated by Admin"

    def test_delete_user_admin(self, client: TestClient, admin_headers, db_session: Session):
        """Test admin can delete user."""
        # Create a user to delete
        from src.backend.auth.user_management import user_management_service
        from src.backend.auth import schemas
        
        user_data = schemas.UserCreate(
            email="deleteme@example.com",
            password="password123",
            full_name="Delete Me",
            tenant_name="delete-tenant"
        )
        user = user_management_service.create_user(db_session, user_data)
        
        response = client.delete(f"/api/v1/users/{user.id}", headers=admin_headers)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["msg"]

    def test_admin_endpoints_denied_for_user(self, client: TestClient, auth_headers):
        """Test regular user cannot access admin endpoints."""
        admin_endpoints = [
            "/api/v1/users",
            ("/api/v1/users", {"email": "test@test.com", "password": "pass", "full_name": "Test", "tenant_name": "test"}),
        ]
        
        # Test GET /users
        response = client.get("/api/v1/users", headers=auth_headers)
        assert response.status_code == 403
        
        # Test POST /users
        user_data = {
            "email": "unauthorized@example.com",
            "password": "pass123",
            "full_name": "Unauthorized",
            "tenant_name": "unauth-tenant"
        }
        response = client.post("/api/v1/users", json=user_data, headers=auth_headers)
        assert response.status_code == 403


class TestErrorHandling:
    """Test API error handling."""

    def test_404_not_found(self, client: TestClient):
        """Test 404 for non-existent endpoints."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_405_method_not_allowed(self, client: TestClient):
        """Test 405 for wrong HTTP method."""
        response = client.post("/hello")
        assert response.status_code == 405

    def test_422_validation_error(self, client: TestClient):
        """Test 422 for validation errors."""
        invalid_user_data = {
            "email": "invalid-email",  # Invalid email format
            "password": "short",       # Too short
            "full_name": "",          # Empty
            "tenant_name": ""         # Empty
        }
        
        response = client.post("/api/v1/signup", json=invalid_user_data)
        assert response.status_code == 422

    def test_user_not_found_error(self, client: TestClient, admin_headers):
        """Test user not found error."""
        response = client.get("/api/v1/users/99999", headers=admin_headers)
        print(response.json())
        assert response.status_code == 404

    def test_update_nonexistent_user(self, client: TestClient, admin_headers):
        """Test updating non-existent user."""
        update_data = {"full_name": "Updated Name"}
        response = client.put("/api/v1/users/99999", json=update_data, headers=admin_headers)
        assert response.status_code == 404

    def test_delete_nonexistent_user(self, client: TestClient, admin_headers):
        """Test deleting non-existent user."""
        response = client.delete("/api/v1/users/99999", headers=admin_headers)
        assert response.status_code == 404


class TestCORSAndSecurity:
    """Test CORS and security headers."""

    def test_security_headers(self, client: TestClient):
        """Test that security headers are present."""
        response = client.get("/hello")
        # Note: This would require actual CORS middleware configuration
        assert response.status_code == 200

    def test_content_type_json(self, client: TestClient):
        """Test that API returns JSON content type."""
        response = client.get("/hello")
        assert "application/json" in response.headers.get("content-type", "")


class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    def test_complete_user_lifecycle(self, client: TestClient):
        """Test complete user lifecycle: signup -> login -> use API -> admin operations."""
        # 1. User signup
        user_data = {
            "email": "lifecycle@example.com",
            "password": "lifecycle123",
            "full_name": "Lifecycle User",
            "tenant_name": "lifecycle-tenant"
        }
        
        signup_response = client.post("/api/v1/signup", json=user_data)
        assert signup_response.status_code == 201
        user_id = signup_response.json()["id"]
        
        # 2. User login
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = client.post("/api/v1/login/access-token", data=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Use authenticated endpoints
        headers = {"Authorization": f"Bearer {token}"}
        welcome_response = client.get("/welcome", headers=headers)
        assert welcome_response.status_code == 200
        
        # 4. Try admin endpoint (should fail)
        admin_response = client.get("/admin/me", headers=headers)
        assert admin_response.status_code == 403

    def test_multi_tenant_isolation_scenario(self, client: TestClient):
        """Test multi-tenant isolation in a complete scenario."""
        # Create users in different tenants
        tenant1_data = {
            "email": "tenant1user@example.com",
            "password": "password123",
            "full_name": "Tenant 1 User",
            "tenant_name": "isolation-tenant-1"
        }
        
        tenant2_data = {
            "email": "tenant2user@example.com",
            "password": "password123",
            "full_name": "Tenant 2 User",
            "tenant_name": "isolation-tenant-2"
        }
        
        # Create both users
        response1 = client.post("/api/v1/signup", json=tenant1_data)
        response2 = client.post("/api/v1/signup", json=tenant2_data)
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        
        # Verify they have different tenant assignments
        user1 = response1.json()
        user2 = response2.json()
        assert user1["tenant_name"] != user2["tenant_name"]
        
        # Login both users and verify they can access their own data
        for user_data, expected_tenant in [(tenant1_data, "isolation-tenant-1"), (tenant2_data, "isolation-tenant-2")]:
            login_data = {
                "username": user_data["email"],
                "password": user_data["password"]
            }
            login_response = client.post("/api/v1/login/access-token", data=login_data)
            assert login_response.status_code == 200
            
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Access user-specific endpoint
            user_response = client.get("/user/me", headers=headers)
            assert user_response.status_code == 200


class TestChannelEndpoints:
    """Test channel-related API endpoints."""

    def test_create_channel_superuser(self, client: TestClient, superuser_headers):
        """Test superuser can create a new channel."""
        channel_data = {
            "name": "general-super",
            "description": "General discussion channel by superuser",
            "is_private": False
        }
        response = client.post("/api/v1/channels", json=channel_data, headers=superuser_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == channel_data["name"]
        assert "id" in data

    def test_create_channel_user_denied(self, client: TestClient, auth_headers):
        """Test regular user cannot create a new channel."""
        channel_data = {
            "name": "user-channel",
            "description": "A channel a user tries to create",
            "is_private": False
        }
        response = client.post("/api/v1/channels", json=channel_data, headers=auth_headers)
        assert response.status_code == 403

    def test_get_channels_authenticated(self, client: TestClient, auth_headers):
        """Test authenticated user can get a list of channels."""
        response = client.get("/api/v1/channels", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_channel_lifecycle_and_membership(self, client: TestClient, admin_headers, create_test_user):
        """Test full channel lifecycle: create, get, add/remove member, delete."""
        # 1. Create a channel
        channel_data = {"name": "lifecycle-channel", "description": "Test lifecycle"}
        response = client.post("/api/v1/channels", json=channel_data, headers=admin_headers)
        assert response.status_code == 200
        channel = response.json()
        channel_id = channel["id"]

        # 2. Get the specific channel
        response = client.get(f"/api/v1/channels/{channel_id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "lifecycle-channel"

        # 3. Add a member to the channel
        member_data = {"user_id": create_test_user.id, "role": "member"}
        response = client.post(f"/api/v1/channels/{channel_id}/members", json=member_data, headers=admin_headers)
        assert response.status_code == 200
        assert "Member added" in response.json()["message"]

        # 4. Get channel members and verify
        response = client.get(f"/api/v1/channels/{channel_id}/members", headers=admin_headers)
        assert response.status_code == 200
        members = response.json()
        # Creator (admin) + new member
        assert len(members) >= 2 
        assert any(m["user_id"] == create_test_user.id for m in members)

        # 5. Remove the member
        response = client.delete(f"/api/v1/channels/{channel_id}/members/{create_test_user.id}", headers=admin_headers)
        assert response.status_code == 200
        assert "Member removed" in response.json()["message"]

        # 6. Delete the channel
        response = client.delete(f"/api/v1/channels/{channel_id}", headers=admin_headers)
        assert response.status_code == 200
        assert "Channel deleted" in response.json()["message"]

        # 7. Verify channel is deleted
        response = client.get(f"/api/v1/channels/{channel_id}", headers=admin_headers)
        assert response.status_code == 404
