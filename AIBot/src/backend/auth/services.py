
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.Backend.core.config import settings
from src.Backend.core.security import get_password_hash, verify_password, create_access_token
from src.Backend.Shared.database import get_db
from src.Backend.Shared.email import send_password_reset_email
from . import models, schemas
import secrets
from datetime import datetime, timedelta

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

def get_user(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def get_tenant_by_name(db: Session, name: str) -> models.Tenant | None:
    return db.query(models.Tenant).filter(models.Tenant.name == name).first()

def create_tenant(db: Session, name: str) -> models.Tenant:
    db_tenant = models.Tenant(name=name)
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = get_user(db=db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    tenant = get_tenant_by_name(db, name=user.tenant_name)
    if not tenant:
        tenant = create_tenant(db, name=user.tenant_name)

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=schemas.UserRole.USER,
        tenant_id=tenant.id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate(*, db: Session, email: str, password: str) -> models.User | None:
    user = get_user(db=db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = schemas.TokenData(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = get_user(db=db, email=token_data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    # In a real app, you might check if the user is active
    return current_user

def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if current_user.role not in [schemas.UserRole.ADMIN, schemas.UserRole.SUPER_USER]:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_active_admin(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    if current_user.role != schemas.UserRole.ADMIN:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

def generate_password_reset_token(email: str) -> str:
    """Generate a password reset token."""
    return create_access_token(email, expires_delta=timedelta(hours=1))

def send_password_reset(db: Session, email: str) -> bool:
    """Send password reset email."""
    user = get_user(db, email)
    if not user:
        return False
    
    reset_token = generate_password_reset_token(email)
    return send_password_reset_email(email, reset_token)

def reset_password(db: Session, token: str, new_password: str) -> bool:
    """Reset password using token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            return False
            
        user = get_user(db, email)
        if not user:
            return False
            
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        return True
    except JWTError:
        return False

def change_user_password(db: Session, user: models.User, new_password: str) -> bool:
    """Change user password."""
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    """Get list of users (admin only)."""
    return db.query(models.User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> models.User | None:
    """Update user (admin only)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
        
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.role is not None:
        user.role = user_update.role
        
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    """Delete user (admin only)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return False
        
    db.delete(user)
    db.commit()
    return True
