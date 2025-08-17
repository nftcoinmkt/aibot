"""
Pytest configuration and shared fixtures for comprehensive testing.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.backend.shared.database_manager import database_manager
from src.backend.auth.user_management import user_management_service
from src.backend.auth import models, schemas
from src.backend.core.security import create_access_token, get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test database tables."""
    database_manager.Base.metadata.create_all(bind=engine)
    app.dependency_overrides[database_manager.get_default_db] = override_get_db
    yield
    database_manager.Base.metadata.drop_all(bind=engine)


# Ensure a clean schema for every test to prevent data leakage across tests
@pytest.fixture(autouse=True)
def _reset_db_schema_between_tests():
    database_manager.Base.metadata.drop_all(bind=engine)
    database_manager.Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)

@pytest.fixture
def db_session():
    """Database session fixture."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user_data():
    """Standard test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "tenant_name": "test-tenant"
    }

@pytest.fixture
def test_admin_data():
    """Admin test user data."""
    return {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "full_name": "Admin User",
        "tenant_name": "admin-tenant"
    }

@pytest.fixture
def test_superuser_data():
    """Super user test data."""
    return {
        "email": "superuser@example.com",
        "password": "superpassword123",
        "full_name": "Super User",
        "tenant_name": "super-tenant"
    }

@pytest.fixture
def create_test_user(db_session, test_user_data):
    """Create a test user in the database."""
    user_create = schemas.UserCreate(**test_user_data)
    user = user_management_service.create_user(db_session, user_create)
    return user

@pytest.fixture
def create_test_admin(db_session, test_admin_data):
    """Create an admin user in the database."""
    from src.backend.auth.models import User, Tenant
    
    # Create tenant
    tenant = Tenant(name=test_admin_data["tenant_name"], database_name=test_admin_data["tenant_name"])
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    
    # Create admin user
    admin_user = User(
        email=test_admin_data["email"],
        full_name=test_admin_data["full_name"],
        hashed_password=get_password_hash(test_admin_data["password"]),
        role=schemas.UserRole.ADMIN,
        tenant_id=tenant.id,
        tenant_name=tenant.name
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user

@pytest.fixture
def user_token(client, test_user_data, create_test_user):
    """Get authentication token for test user."""
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/v1/login/access-token", data=login_data)
    return response.json()["access_token"]

@pytest.fixture
def admin_token(client, test_admin_data, create_test_admin):
    """Get authentication token for admin user."""
    login_data = {
        "username": test_admin_data["email"],
        "password": test_admin_data["password"]
    }
    response = client.post("/api/v1/login/access-token", data=login_data)
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(user_token):
    """Authentication headers for regular user."""
    return {"Authorization": f"Bearer {user_token}"}

@pytest.fixture
def admin_headers(admin_token):
    """Authentication headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}
