
from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from datetime import datetime
from typing import Optional, List


class UserRole(str, Enum):
    ADMIN = "admin"
    SUPER_USER = "super_user"
    USER = "user"


class TenantBase(BaseModel):
    name: str


class TenantCreate(TenantBase):
    pass


class Tenant(TenantBase):
    id: int
    database_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    tenant_name: str


class UserInDBBase(UserBase):
    id: int
    role: UserRole
    tenant_name: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    tenant_name: str


class TokenData(BaseModel):
    email: str | None = None


class Msg(BaseModel):
    msg: str


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None


class UserList(BaseModel):
    users: List[User]
    total: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserStats(BaseModel):
    total_users: int
    active_users: int
    users_by_role: dict
    recent_registrations: int
