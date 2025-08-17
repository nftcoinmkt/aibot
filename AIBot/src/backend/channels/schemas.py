from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChannelBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False
    max_members: int = 100


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None
    max_members: Optional[int] = None


class Channel(ChannelBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChannelMessageBase(BaseModel):
    message: str
    message_type: str = 'user'


class ChannelMessageCreate(ChannelMessageBase):
    pass


class ChannelMessage(ChannelMessageBase):
    id: int
    channel_id: int
    user_id: int
    response: Optional[str] = None
    provider: Optional[str] = None
    created_at: datetime
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    is_archived: bool = False

    class Config:
        from_attributes = True


class ChannelMemberAdd(BaseModel):
    user_id: int
    role: str = 'member'


class ChannelMember(BaseModel):
    user_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class ChannelWithMembers(Channel):
    member_count: int = 0

    class Config:
        from_attributes = True
