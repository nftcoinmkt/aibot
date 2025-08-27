from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from src.backend.core.settings import settings
from src.backend.core.security import get_password_hash, verify_password, create_access_token
from src.backend.shared.database_manager import get_default_db, get_tenant_db, create_tenant_database
from src.backend.shared.email_service import email_service
from .tenant_config import FixedTenants
from . import models, schemas
import secrets
from datetime import datetime, timedelta
from jose import JWTError, jwt


class UserManagementService:
    """Service for managing users and authentication."""

    def get_user_by_email(self, db: Session, email: str) -> Optional[models.User]:
        """Get user by email address."""
        return db.query(models.User).filter(models.User.email == email).first()

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[models.User]:
        """Get user by ID."""
        return db.query(models.User).filter(models.User.id == user_id).first()

    def get_tenant_by_name(self, db: Session, name: str) -> Optional[models.Tenant]:
        """Get tenant by name."""
        return db.query(models.Tenant).filter(models.Tenant.name == name).first()

    def create_tenant(self, db: Session, name: str) -> models.Tenant:
        """Create a new tenant with its own database."""
        # Create tenant record in default database
        db_tenant = models.Tenant(name=name)
        db.add(db_tenant)
        db.commit()
        db.refresh(db_tenant)
        
        # Create dedicated database for this tenant
        create_tenant_database(name)
        
        return db_tenant

    def create_user(self, db: Session, user: schemas.UserCreate) -> models.User:
        """Create a new user."""
        # Validate tenant
        if not FixedTenants.is_valid_tenant(user.tenant_name):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid organization. Please select from available organizations.",
            )

        # Check if user already exists by email (only if email is provided)
        if user.email:
            db_user = self.get_user_by_email(db=db, email=user.email)
            if db_user:
                raise HTTPException(
                    status_code=400,
                    detail="The user with this email already exists in the system.",
                )
        
        # Get or create tenant
        tenant = self.get_tenant_by_name(db, name=user.tenant_name)
        if not tenant:
            tenant = self.create_tenant(db, name=user.tenant_name)

        # Create user in default database
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            role=schemas.UserRole.USER,
            tenant_id=tenant.id,
            tenant_name=tenant.name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Send welcome email (optional - don't fail signup if email fails)
        if user.email:
            try:
                email_service.send_welcome_email(user.email, user.full_name, tenant.name)
            except Exception as e:
                print(f"Warning: Failed to send welcome email to {user.email}: {e}")
                # Continue with signup even if email fails

        return db_user

    def create_user_for_invite(self, db: Session, user: schemas.UserCreateInvite) -> models.User:
        """Create user for invite - email is optional."""
        tenant = self.get_tenant_by_name(db, user.tenant_name)
        if not tenant:
            raise ValueError(f"Tenant '{user.tenant_name}' not found")
        
        # Check if email is provided and if user already exists
        if user.email:
            existing_user = self.get_user_by_email(db, user.email)
            if existing_user:
                raise ValueError("User with this email already exists")
        
        hashed_password = get_password_hash(user.password)
        
        # Create user with or without email
        db_user = models.User(
            email=user.email,  # Can be None now that email is nullable
            full_name=user.full_name,
            hashed_password=hashed_password,
            role=schemas.UserRole.USER,
            tenant_id=tenant.id,
            tenant_name=tenant.name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Only send welcome email if email is provided
        if user.email:
            try:
                email_service.send_welcome_email(user.email, user.full_name, tenant.name)
            except Exception as e:
                print(f"Warning: Failed to send welcome email to {user.email}: {e}")
        
        return db_user

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[models.User]:
        """Authenticate user with email and password."""
        user = self.get_user_by_email(db=db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def get_user_by_phone(self, db: Session, phone_number: str) -> Optional[models.User]:
        """Get user by phone number via `UserContact`."""
        contact = (
            db.query(models.UserContact)
            .filter(models.UserContact.phone_number == phone_number)
            .first()
        )
        if not contact:
            return None
        return self.get_user_by_id(db, contact.user_id)

    def get_user_by_identifier(self, db: Session, identifier: str) -> Optional[models.User]:
        """Get user by email (if contains '@') or by phone number otherwise."""
        if "@" in identifier:
            return self.get_user_by_email(db, identifier)
        return self.get_user_by_phone(db, identifier)

    def authenticate_by_identifier(self, db: Session, identifier: str, password: str) -> Optional[models.User]:
        """Authenticate using either email or phone as identifier."""
        user = self.get_user_by_identifier(db, identifier)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def link_phone_to_user(self, db: Session, user: models.User, phone_number: str, verified: bool = False) -> models.UserContact:
        """Attach a phone number to a user, creating or updating `UserContact`."""
        existing = (
            db.query(models.UserContact)
            .filter(models.UserContact.phone_number == phone_number)
            .first()
        )
        if existing:
            # If phone already linked to someone else, prevent takeover
            if existing.user_id != user.id:
                raise HTTPException(status_code=400, detail="Phone number already linked to another user")
            if verified and not existing.is_verified:
                existing.is_verified = True
                db.commit()
                db.refresh(existing)
            return existing

        contact = models.UserContact(
            user_id=user.id,
            phone_number=phone_number,
            is_verified=verified,
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    def update_user(self, db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
        """Update user information."""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None
            
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.role is not None:
            user.role = user_update.role
            
        db.commit()
        db.refresh(user)
        return user

    def delete_user(self, db: Session, user_id: int) -> bool:
        """Delete user."""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
            
        db.delete(user)
        db.commit()
        return True

    def get_users_list(self, db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
        """Get list of users with pagination."""
        print("get_users_list")
        return db.query(models.User).offset(skip).limit(limit).all()

    def change_user_password(self, db: Session, user: models.User, new_password: str) -> bool:
        """Change user password."""
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True


class PasswordResetService:
    """Service for handling password reset operations."""

    def generate_reset_token(self, email: str) -> str:
        """Generate a password reset token."""
        return create_access_token(email, expires_delta=timedelta(hours=1))

    def send_password_reset_email(self, db: Session, email: str) -> bool:
        """Send password reset email."""
        user_service = UserManagementService()
        user = user_service.get_user_by_email(db, email)
        if not user:
            return False
        
        reset_token = self.generate_reset_token(email)
        return email_service.send_password_reset_email(email, reset_token)

    def reset_password_with_token(self, db: Session, token: str, new_password: str) -> bool:
        """Reset password using token."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            if not email:
                return False
                
            user_service = UserManagementService()
            user = user_service.get_user_by_email(db, email)
            if not user:
                return False
                
            user.hashed_password = get_password_hash(new_password)
            db.commit()
            return True
        except JWTError:
            return False


# Global service instances
user_management_service = UserManagementService()
password_reset_service = PasswordResetService()
