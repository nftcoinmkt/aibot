from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.backend.core.settings import settings
from src.backend.shared.database_manager import get_master_db
from .models import User
from .schemas import TokenData


security = HTTPBearer()


async def get_current_user_from_token(token: str) -> User:
    """
    Get current user from JWT token for WebSocket authentication.
    """
    print(f"🔐 WebSocket auth: Validating token {token[:20]}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Support both email and user_id in JWT tokens
        sub = payload.get("sub")
        user_id = payload.get("user_id")
        
        print(f"📧 Extracted sub from token: {sub}")
        print(f"🆔 Extracted user_id from token: {user_id}")
        
        if user_id:
            token_data = TokenData(user_id=user_id)
        elif sub:
            token_data = TokenData(email=sub)
        else:
            print("❌ No identifier found in token")
            raise credentials_exception
        print(f"✅ Token data created successfully")
    except JWTError as e:
        print(f"❌ JWT decode error: {e}")
        raise credentials_exception
    
    # Get user from master database
    db_generator = get_master_db()
    db = next(db_generator)
    
    try:
        # Try to get user by user_id first, then by email
        if token_data.user_id:
            user = db.query(User).filter(User.id == token_data.user_id).first()
            print(f"🔍 Looking up user by ID: {token_data.user_id}")
        elif token_data.email:
            user = db.query(User).filter(User.email == token_data.email).first()
            print(f"🔍 Looking up user by email: {token_data.email}")
        else:
            user = None
            
        if user is None:
            print(f"❌ User not found for identifier: {token_data.user_id or token_data.email}")
            raise credentials_exception
        print(f"✅ User found: {user.email or f'ID:{user.id}'} (ID: {user.id})")
        return user
    finally:
        db.close()
