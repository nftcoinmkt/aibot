import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from typing import Dict
from types import SimpleNamespace

from src.backend.core.settings import settings, get_tenant_database_uri

Base = declarative_base()

# Default database engine for system operations
default_engine = create_engine(
    settings.DEFAULT_DATABASE_URI, 
    connect_args={"check_same_thread": False}
)
DefaultSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=default_engine)

# Tenant database engines cache
tenant_engines: Dict[str, any] = {}
tenant_sessions: Dict[str, any] = {}


def ensure_tenant_database_directory():
    """Ensure tenant database directory exists."""
    Path(settings.TENANT_DATABASE_PATH).mkdir(parents=True, exist_ok=True)


def get_tenant_engine(tenant_name: str):
    """Get or create database engine for a specific tenant."""
    if tenant_name not in tenant_engines:
        ensure_tenant_database_directory()
        database_uri = get_tenant_database_uri(tenant_name)
        tenant_engines[tenant_name] = create_engine(
            database_uri, 
            connect_args={"check_same_thread": False}
        )
        # Create tables for new tenant
        Base.metadata.create_all(bind=tenant_engines[tenant_name])
    
    return tenant_engines[tenant_name]


def get_tenant_session_local(tenant_name: str):
    """Get SessionLocal class for a specific tenant."""
    if tenant_name not in tenant_sessions:
        engine = get_tenant_engine(tenant_name)
        tenant_sessions[tenant_name] = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=engine
        )
    
    return tenant_sessions[tenant_name]


def get_default_db():
    """Get default database session (for system operations)."""
    db = DefaultSessionLocal()
    print("get_default_db")
    try:
        yield db
    finally:
        db.close()


def get_tenant_db(tenant_name: str):
    """Get tenant-specific database session."""
    SessionLocal = get_tenant_session_local(tenant_name)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tenant_database(tenant_name: str):
    """Create database for a new tenant."""
    engine = get_tenant_engine(tenant_name)
    Base.metadata.create_all(bind=engine)
    return engine


def list_tenant_databases():
    """List all existing tenant databases."""
    ensure_tenant_database_directory()
    db_path = Path(settings.TENANT_DATABASE_PATH)
    return [f.stem for f in db_path.glob("*.db")]

# Backwards-compatible namespace export so tests can import
# `from src.backend.shared.database_manager import database_manager`
database_manager = SimpleNamespace(
    Base=Base,
    default_engine=default_engine,
    DefaultSessionLocal=DefaultSessionLocal,
    ensure_tenant_database_directory=ensure_tenant_database_directory,
    get_tenant_engine=get_tenant_engine,
    get_tenant_session_local=get_tenant_session_local,
    get_default_db=get_default_db,
    get_tenant_db=get_tenant_db,
    create_tenant_database=create_tenant_database,
    list_tenant_databases=list_tenant_databases,
)
