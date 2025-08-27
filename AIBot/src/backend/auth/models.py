
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLAlchemyEnum, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy import event

from src.backend.shared.database_manager import MasterBase
from .schemas import UserRole


class Tenant(MasterBase):
    __tablename__ = "tenants"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    database_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="tenant")


# Ensure database_name defaults to name when not provided
@event.listens_for(Tenant, "before_insert")
def _tenant_set_database_name(mapper, connection, target):
    if not getattr(target, "database_name", None):
        target.database_name = target.name


class User(MasterBase):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False, default=UserRole.USER)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    tenant_name = Column(String, nullable=False)  # For easier queries
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="users")


class UserContact(MasterBase):
    __tablename__ = "user_contacts"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OtpRequest(MasterBase):
    __tablename__ = "otp_requests"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    # 'email' or 'phone'
    contact_type = Column(String, nullable=False)
    contact = Column(String, index=True, nullable=False)
    purpose = Column(String, index=True, nullable=False)  # 'signup' | 'login' | 'invite'
    tenant_name = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    code = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    consumed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # MessageCentral specific fields
    messagecentral_verification_id = Column(String, nullable=True)
    messagecentral_timeout = Column(String, nullable=True)
