from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session
from datetime import datetime

from src.backend.core.settings import settings
from src.backend.core.security import verify_password
from src.backend.shared.database_manager import get_master_db
from .user_management import user_management_service
from . import models, schemas


reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


class AuthenticationService:
    """Service for handling authentication and authorization."""

    def get_current_user(
        self, db: Session = Depends(get_master_db), token: str = Depends(reusable_oauth2)
    ) -> models.User:
        """Get current user from JWT token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            # Support both email and user_id in JWT tokens
            sub = payload.get("sub")
            user_id = payload.get("user_id")
            
            if user_id:
                token_data = schemas.TokenData(user_id=user_id)
            else:
                token_data = schemas.TokenData(email=sub)
        except (JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )

        # Try to get user by user_id first, then by email
        if token_data.user_id:
            user = user_management_service.get_user_by_id(db=db, user_id=token_data.user_id)
        elif token_data.email:
            user = user_management_service.get_user_by_email(db=db, email=token_data.email)
        else:
            user = None
            
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user

    def get_current_active_user(
        self, current_user: models.User = Depends(get_current_user)
    ) -> models.User:
        """Get current active user."""
        return current_user

    def get_current_active_superuser(
        self, current_user: models.User = Depends(get_current_user)
    ) -> models.User:
        """Get current user if they are super user or admin."""
        if current_user.role not in [schemas.UserRole.ADMIN, schemas.UserRole.SUPER_USER]:
            raise HTTPException(
                status_code=403, detail="The user doesn't have enough privileges"
            )
        return current_user

    def get_current_active_admin(
        self, current_user: models.User = Depends(get_current_user)
    ) -> models.User:
        """Get current user if they are admin."""
        if current_user.role != schemas.UserRole.ADMIN:
            raise HTTPException(
                status_code=403, detail="The user doesn't have enough privileges"
            )
        return current_user

    def verify_user_access_to_tenant(
        self, current_user: models.User, tenant_name: str
    ) -> bool:
        """Verify if user has access to specific tenant."""
        return current_user.tenant_name == tenant_name or current_user.role == schemas.UserRole.ADMIN

    def authenticate_user(self, db: Session, email: str, password: str) -> models.User | None:
        """Authenticate user with email and password."""
        return user_management_service.authenticate_user(db, email, password)

    def get_user_from_token(self, token: str) -> models.User | None:
        """Get user from JWT token without FastAPI dependencies."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            email = payload.get("sub")
            if not email:
                return None
            
            # Get database session (master)
            from src.backend.shared.database_manager import MasterSessionLocal
            db = MasterSessionLocal()
            try:
                user = user_management_service.get_user_by_email(db=db, email=email)
                if not user or not user.is_active:
                    return None
                return user
            finally:
                db.close()
                
        except (JWTError, ValidationError):
            return None


# Global authentication service instance
authentication_service = AuthenticationService()


# Dependency functions for FastAPI
def get_current_user(
    db: Session = Depends(get_master_db),
    token: str = Depends(reusable_oauth2)
) -> models.User:
    return authentication_service.get_current_user(db, token)


def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    return authentication_service.get_current_active_user(current_user)


def get_current_active_superuser(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    return authentication_service.get_current_active_superuser(current_user)


def get_current_active_admin(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    return authentication_service.get_current_active_admin(current_user)


def get_user_from_token(token: str) -> models.User | None:
    """Get user from JWT token without FastAPI dependencies."""
    return authentication_service.get_user_from_token(token)
