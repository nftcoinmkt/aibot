from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ChannelRole(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"


class MessageType(str, Enum):
    USER = "user"
    AI = "ai"
    SYSTEM = "system"


class ChannelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_private: bool = False


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_private: Optional[bool] = None
    is_active: Optional[bool] = None


class Channel(ChannelBase):
    id: int
    created_by: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChannelWithMembers(Channel):
    member_count: int
    user_role: Optional[str] = None  # Current user's role in this channel


class ChannelMember(BaseModel):
    user_id: int
    role: ChannelRole
    joined_at: datetime


class ChannelMemberAdd(BaseModel):
    user_id: int
    role: ChannelRole = ChannelRole.MEMBER


class ChannelMemberUpdate(BaseModel):
    role: ChannelRole


class ChannelMessageBase(BaseModel):
    message: str = Field(..., min_length=1)


class ChannelMessageCreate(ChannelMessageBase):
    channel_id: int


class ChannelMessage(ChannelMessageBase):
    id: int
    channel_id: int
    user_id: int
    response: Optional[str] = None
    provider: Optional[str] = None
    message_type: MessageType
    created_at: datetime
    message_length: Optional[int] = None
    response_length: Optional[int] = None
    processing_time: Optional[str] = None

    class Config:
        from_attributes = True


class ChannelStats(BaseModel):
    total_channels: int
    active_channels: int
    private_channels: int
    total_messages: int
    channels_by_creator: dict
