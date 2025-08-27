
from datetime import timedelta
from typing import List
import secrets

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.backend.core.settings import settings
from src.backend.core.security import create_access_token
from src.backend.shared.database_manager import get_master_db
from .user_management import user_management_service, password_reset_service
from .authentication_service import get_current_active_user, get_current_active_admin
from .tenant_config import FixedTenants
from . import models, schemas
from .otp_service import otp_service

router = APIRouter()

@router.get("/tenants")
def get_available_tenants():
    """
    Get list of available tenants/organizations for signup.
    """
    return {
        "tenants": FixedTenants.get_available_tenants()
    }

@router.post("/signup", response_model=schemas.User, status_code=201)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_master_db)):
    """
    Create new user.
    """
    user = user_management_service.create_user(db=db, user=user_in)
    return user

@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(get_master_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = user_management_service.authenticate_user(
        db=db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.email, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,  # Include user ID in response
        "tenant_name": user.tenant_name,
    }

@router.post("/forgot-password", response_model=schemas.Msg)
def forgot_password(email: str = Body(...), db: Session = Depends(get_master_db)):
    """
    Send password reset email.
    """
    success = password_reset_service.send_password_reset_email(db, email)
    if success:
        return {"msg": "Password recovery email sent"}
    else:
        return {"msg": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password", response_model=schemas.Msg)
def reset_password(
    reset_data: schemas.PasswordReset,
    db: Session = Depends(get_master_db)
):
    """
    Reset password using token.
    """
    success = password_reset_service.reset_password_with_token(db, reset_data.token, reset_data.new_password)
    if success:
        return {"msg": "Password updated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

@router.post("/change-password", response_model=schemas.Msg)
def change_password(
    password_data: schemas.PasswordChange,
    db: Session = Depends(get_master_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Change password.
    """
    if not user_management_service.authenticate_user(db=db, email=current_user.email, password=password_data.current_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    user_management_service.change_user_password(db, current_user, password_data.new_password)
    return {"msg": "Password changed successfully"}

@router.post("/signout", response_model=schemas.Msg)
def signout(current_user: models.User = Depends(get_current_active_user)):
    """
    Sign out current user.
    Since JWT tokens are stateless, this endpoint simply confirms the user is authenticated.
    The client should remove the token from storage.
    """
    return {"msg": f"User {current_user.email} signed out successfully"}

# User endpoints for regular users
@router.get("/users/list", response_model=List[schemas.User])
def get_users_for_regular_user(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_master_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get list of users (for channel management by regular users).
    """
    users = user_management_service.get_users_list(db, skip=skip, limit=limit)
    return users

# Admin endpoints
@router.get("/users", response_model=List[schemas.User])
def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_master_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """
    Get list of users (admin only).
    """
    users = user_management_service.get_users_list(db, skip=skip, limit=limit)
    return users

@router.post("/users", response_model=schemas.User, status_code=201)
def create_user_admin(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_master_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """
    Create user (admin only).
    """
    user = user_management_service.create_user(db=db, user=user_in)
    return user

@router.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_master_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """
    Update user (admin only).
    """
    user = user_management_service.update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/users/{user_id}", response_model=schemas.Msg)
def delete_user(
    user_id: int,
    db: Session = Depends(get_master_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """
    Delete user (admin only).
    """
    success = user_management_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"msg": "User deleted successfully"}

# --- OTP and Identifier-based Auth Endpoints ---

@router.post("/otp/request")
def otp_request(req: schemas.OTPRequestIn, db: Session = Depends(get_master_db)):
    """Request an OTP for signup or login. Throttled by settings.OTP_RESEND_INTERVAL_SECONDS."""
    
    # Validate tenant for signup
    if req.purpose == schemas.OtpPurpose.signup:
        if not req.tenant_name or not FixedTenants.is_valid_tenant(req.tenant_name):
            raise HTTPException(status_code=400, detail="Valid organization is required for signup")
        
        # Check if user already exists with this contact
        existing_user = None
        if req.contact_type == schemas.ContactType.email:
            existing_user = user_management_service.get_user_by_email(db, req.contact)
        elif req.contact_type == schemas.ContactType.phone:
            existing_user = user_management_service.get_user_by_phone(db, req.contact)
        
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this contact already exists")
    
    elif req.purpose == schemas.OtpPurpose.login:
        # For login, ensure user exists
        existing_user = None
        if req.contact_type == schemas.ContactType.email:
            existing_user = user_management_service.get_user_by_email(db, req.contact)
        elif req.contact_type == schemas.ContactType.phone:
            existing_user = user_management_service.get_user_by_phone(db, req.contact)
        
        if not existing_user:
            # Don't reveal if user doesn't exist
            return {"sent": False, "retry_after": settings.OTP_RESEND_INTERVAL_SECONDS}

    sent, retry_after = otp_service.request_otp(
        db,
        contact_type=req.contact_type,
        contact=req.contact,
        purpose=req.purpose,
        tenant_name=req.tenant_name,
    )
    
    return {"sent": sent, "retry_after": retry_after}


@router.post("/otp/verify-signup", response_model=schemas.Token)
def otp_verify_signup(req: schemas.OTPVerifySignupIn, db: Session = Depends(get_master_db)):
    if not FixedTenants.is_valid_tenant(req.tenant_name):
        raise HTTPException(status_code=400, detail="Invalid organization. Please select from available organizations.")

    # Validate OTP first
    otp_service.verify_otp(
        db,
        contact_type=req.contact_type,
        contact=req.contact,
        purpose=schemas.OtpPurpose.signup,
        code=req.code,
        tenant_name=req.tenant_name,
    )

    # Determine primary contact and email
    email = None
    phone_number = None
    
    if req.contact_type == schemas.ContactType.email:
        email = req.contact
        phone_number = req.phone_number  # Optional phone from request
    elif req.contact_type == schemas.ContactType.phone:
        phone_number = req.contact
        email = req.email  # Optional email from request
        
        # If no email provided for phone signup, generate one or require it
        if not email:
            raise HTTPException(status_code=400, detail="Email is required for account creation")

    # Ensure no duplicate users
    if email and user_management_service.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="A user with this email already exists")
    
    if phone_number and user_management_service.get_user_by_phone(db, phone_number):
        raise HTTPException(status_code=400, detail="A user with this phone number already exists")

    # Validate password requirement
    if not req.password:
        raise HTTPException(status_code=400, detail="Password is required")

    # Create user with email as primary identifier
    user_in = schemas.UserCreate(
        email=email,
        password=req.password,
        full_name=req.full_name,
        tenant_name=req.tenant_name,
    )
    user = user_management_service.create_user(db=db, user=user_in)

    # Link phone if provided
    if phone_number:
        user_management_service.link_phone_to_user(db, user, phone_number, verified=True)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.email, expires_delta=access_token_expires)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "tenant_name": user.tenant_name,
    }

# Invite functionality removed - signup is now open to all valid tenants


@router.post("/otp/verify-login", response_model=schemas.Token)
def otp_verify_login(req: schemas.OTPVerifyLoginIn, db: Session = Depends(get_master_db)):
    # Determine contact type from identifier
    contact_type = schemas.ContactType.email if "@" in req.identifier else schemas.ContactType.phone
    
    otp_service.verify_otp(
        db,
        contact_type=contact_type,
        contact=req.identifier,
        purpose=schemas.OtpPurpose.login,
        code=req.code,
    )

    user = user_management_service.get_user_by_identifier(db, req.identifier)
    if not user:
        raise HTTPException(status_code=400, detail="Account not found")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.email, expires_delta=access_token_expires)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "tenant_name": user.tenant_name,
    }


@router.post("/login/identifier", response_model=schemas.Token)
def login_by_identifier(
    req: schemas.LoginByIdentifierRequest,
    db: Session = Depends(get_master_db),
):
    """Login using either email or phone number plus password."""
    user = user_management_service.authenticate_by_identifier(db=db, identifier=req.identifier, password=req.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.email, expires_delta=access_token_expires)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "tenant_name": user.tenant_name,
    }


@router.post("/otp/reset-password")
def reset_password_with_otp(
    req: schemas.OTPResetPasswordIn,
    db: Session = Depends(get_master_db),
):
    """Reset password using OTP verification."""
    # Verify OTP
    otp_request = otp_service.verify_otp(
        db,
        contact_type=req.contact_type,
        contact=req.contact,
        purpose=schemas.OtpPurpose.reset_password,
        code=req.code,
    )
    
    # Find user by contact
    if req.contact_type == schemas.ContactType.email:
        user = user_management_service.get_user_by_email(db, req.contact)
    else:
        user = user_management_service.get_user_by_phone(db, req.contact)
    
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    # Update password
    user_management_service.change_user_password(db, user, req.new_password)
    
    return {"message": "Password reset successfully"}