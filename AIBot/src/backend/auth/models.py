
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLAlchemyEnum, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import event

from src.backend.shared.database_manager import Base
from .schemas import UserRole


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    database_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant")


# Ensure database_name defaults to name when not provided
@event.listens_for(Tenant, "before_insert")
def _tenant_set_database_name(mapper, connection, target):
    if not getattr(target, "database_name", None):
        target.database_name = target.name


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False, default=UserRole.USER)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    tenant_name = Column(String, nullable=False)  # For easier queries
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="users")
