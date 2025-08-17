"""
Comprehensive tests for user management functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.auth.user_management import user_management_service, password_reset_service
from src.backend.auth import schemas, models
from src.backend.core.security import verify_password


class TestUserManagement:
    """Test user management service functionality."""

    def test_create_user_success(self, db_session: Session):
        """Test successful user creation."""
        user_data = schemas.UserCreate(
            email="newuser@example.com",
            password="newpassword123",
            full_name="New User",
            tenant_name="new-tenant"
        )
        
        user = user_management_service.create_user(db_session, user_data)
        
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.role == schemas.UserRole.USER
        assert user.tenant_name == "new-tenant"
        assert user.is_active is True
        assert verify_password("newpassword123", user.hashed_password)

    def test_create_user_duplicate_email(self, db_session: Session, create_test_user):
        """Test creating user with duplicate email fails."""
        user_data = schemas.UserCreate(
            email=create_test_user.email,
            password="anotherpassword123",
            full_name="Another User",
            tenant_name="another-tenant"
        )
        
        with pytest.raises(Exception):  # Should raise HTTPException
            user_management_service.create_user(db_session, user_data)

    def test_authenticate_user_success(self, db_session: Session, create_test_user, test_user_data):
        """Test successful user authentication."""
        user = user_management_service.authenticate_user(
            db_session, test_user_data["email"], test_user_data["password"]
        )
        
        assert user is not None
        assert user.email == test_user_data["email"]

    def test_authenticate_user_wrong_password(self, db_session: Session, create_test_user, test_user_data):
        """Test authentication with wrong password."""
        user = user_management_service.authenticate_user(
            db_session, test_user_data["email"], "wrongpassword"
        )
        
        assert user is None

    def test_authenticate_user_nonexistent(self, db_session: Session):
        """Test authentication with nonexistent user."""
        user = user_management_service.authenticate_user(
            db_session, "nonexistent@example.com", "password"
        )
        
        assert user is None

    def test_get_user_by_email(self, db_session: Session, create_test_user):
        """Test getting user by email."""
        user = user_management_service.get_user_by_email(db_session, create_test_user.email)
        
        assert user is not None
        assert user.id == create_test_user.id

    def test_get_user_by_id(self, db_session: Session, create_test_user):
        """Test getting user by ID."""
        user = user_management_service.get_user_by_id(db_session, create_test_user.id)
        
        assert user is not None
        assert user.email == create_test_user.email

    def test_update_user(self, db_session: Session, create_test_user):
        """Test updating user information."""
        update_data = schemas.UserUpdate(
            full_name="Updated Name",
            role=schemas.UserRole.SUPER_USER
        )
        
        updated_user = user_management_service.update_user(db_session, create_test_user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.full_name == "Updated Name"
        assert updated_user.role == schemas.UserRole.SUPER_USER

    def test_delete_user(self, db_session: Session, create_test_user):
        """Test deleting user."""
        user_id = create_test_user.id
        
        success = user_management_service.delete_user(db_session, user_id)
        assert success is True
        
        # Verify user is deleted
        deleted_user = user_management_service.get_user_by_id(db_session, user_id)
        assert deleted_user is None

    def test_get_users_list(self, db_session: Session):
        """Test getting users list with pagination."""
        # Create multiple users
        for i in range(5):
            user_data = schemas.UserCreate(
                email=f"listuser{i}@example.com",
                password="password123",
                full_name=f"List User {i}",
                tenant_name=f"list-tenant-{i}"
            )
            user_management_service.create_user(db_session, user_data)
        
        users = user_management_service.get_users_list(db_session, skip=0, limit=10)
        assert len(users) >= 5

    def test_change_user_password(self, db_session: Session, create_test_user):
        """Test changing user password."""
        new_password = "newpassword456"
        
        success = user_management_service.change_user_password(db_session, create_test_user, new_password)
        assert success is True
        
        # Verify new password works
        db_session.refresh(create_test_user)
        assert verify_password(new_password, create_test_user.hashed_password)


class TestPasswordReset:
    """Test password reset functionality."""

    def test_generate_reset_token(self):
        """Test generating password reset token."""
        email = "test@example.com"
        token = password_reset_service.generate_reset_token(email)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_send_password_reset_email_existing_user(self, db_session: Session, create_test_user):
        """Test sending password reset email for existing user."""
        success = password_reset_service.send_password_reset_email(db_session, create_test_user.email)
        # In test environment, this should return True (email service is mocked)
        assert success is True

    def test_send_password_reset_email_nonexistent_user(self, db_session: Session):
        """Test sending password reset email for nonexistent user."""
        success = password_reset_service.send_password_reset_email(db_session, "nonexistent@example.com")
        assert success is False

    def test_reset_password_with_valid_token(self, db_session: Session, create_test_user):
        """Test resetting password with valid token."""
        token = password_reset_service.generate_reset_token(create_test_user.email)
        new_password = "resetpassword123"
        
        success = password_reset_service.reset_password_with_token(db_session, token, new_password)
        assert success is True
        
        # Verify password was changed
        db_session.refresh(create_test_user)
        assert verify_password(new_password, create_test_user.hashed_password)

    def test_reset_password_with_invalid_token(self, db_session: Session):
        """Test resetting password with invalid token."""
        invalid_token = "invalid.token.here"
        new_password = "resetpassword123"
        
        success = password_reset_service.reset_password_with_token(db_session, invalid_token, new_password)
        assert success is False


class TestTenantManagement:
    """Test tenant management functionality."""

    def test_create_tenant(self, db_session: Session):
        """Test creating a new tenant."""
        tenant_name = "new-test-tenant"
        
        tenant = user_management_service.create_tenant(db_session, tenant_name)
        
        assert tenant.name == tenant_name
        assert tenant.is_active is True
        assert tenant.id is not None

    def test_get_tenant_by_name(self, db_session: Session):
        """Test getting tenant by name."""
        tenant_name = "search-tenant"
        created_tenant = user_management_service.create_tenant(db_session, tenant_name)
        
        found_tenant = user_management_service.get_tenant_by_name(db_session, tenant_name)
        
        assert found_tenant is not None
        assert found_tenant.id == created_tenant.id

    def test_tenant_user_relationship(self, db_session: Session):
        """Test relationship between tenant and users."""
        user_data = schemas.UserCreate(
            email="tenantuser@example.com",
            password="password123",
            full_name="Tenant User",
            tenant_name="relationship-tenant"
        )
        
        user = user_management_service.create_user(db_session, user_data)
        tenant = user_management_service.get_tenant_by_name(db_session, "relationship-tenant")
        
        assert user.tenant_id == tenant.id
        assert user.tenant_name == tenant.name
