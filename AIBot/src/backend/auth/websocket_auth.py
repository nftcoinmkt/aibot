from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.backend.core.settings import settings
from src.backend.shared.database_manager import get_default_db
from .models import User
from .schemas import TokenData


security = HTTPBearer()


async def get_current_user_from_token(token: str) -> User:
    """
    Get current user from JWT token for WebSocket authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    db_generator = get_default_db()
    db = next(db_generator)
    
    try:
        user = db.query(User).filter(User.email == token_data.username).first()
        if user is None:
            raise credentials_exception
        return user
    finally:
        db.close()
