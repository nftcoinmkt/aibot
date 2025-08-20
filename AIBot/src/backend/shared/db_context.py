from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session

from .database_manager import get_tenant_db, get_default_db


@contextmanager
def get_tenant_db_context(tenant_name: str) -> Generator[Session, None, None]:
    """
    Context manager for tenant-specific database sessions.
    Automatically handles session creation and cleanup.
    
    Usage:
        with get_tenant_db_context(tenant_name) as db:
            # perform database operations
            pass
    """
    db_generator = get_tenant_db(tenant_name)
    db = next(db_generator)
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_default_db_context() -> Generator[Session, None, None]:
    """
    Context manager for default database sessions.
    Automatically handles session creation and cleanup.
    
    Usage:
        with get_default_db_context() as db:
            # perform database operations
            pass
    """
    db_generator = get_default_db()
    db = next(db_generator)
    try:
        yield db
    finally:
        db.close()
