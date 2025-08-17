
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.backend.core.settings import settings
from src.backend.core.security import create_access_token
from src.backend.shared.database_manager import get_default_db
from .user_management import user_management_service, password_reset_service
from .authentication_service import get_current_active_user, get_current_active_admin
from . import models, schemas

router = APIRouter()

@router.post("/signup", response_model=schemas.User, status_code=201)
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_default_db)):
    """
    Create new user.
    """
    user = user_management_service.create_user(db=db, user=user_in)
    return user

@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(get_default_db), form_data: OAuth2PasswordRequestForm = Depends()
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
    }

@router.post("/forgot-password", response_model=schemas.Msg)
def forgot_password(email: str = Body(...), db: Session = Depends(get_default_db)):
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
    db: Session = Depends(get_default_db)
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
    db: Session = Depends(get_default_db),
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
    db: Session = Depends(get_default_db),
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
    db: Session = Depends(get_default_db),
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
    db: Session = Depends(get_default_db),
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
    db: Session = Depends(get_default_db),
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
    db: Session = Depends(get_default_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """
    Delete user (admin only).
    """
    success = user_management_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"msg": "User deleted successfully"}
