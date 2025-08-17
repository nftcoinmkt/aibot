
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    provider: str

class ChatHistory(BaseModel):
    id: int
    message: str
    response: str
    provider: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatHistoryList(BaseModel):
    messages: List[ChatHistory]
    total: int

class ChatMessageResponse(BaseModel):
    id: int
    channel_id: int
    user_id: int
    message: str
    response: Optional[str] = None
    provider: Optional[str] = None
    message_type: str  # 'user' or 'ai'
    created_at: datetime

    class Config:
        from_attributes = True

class ChannelChatResponse(BaseModel):
    messages: List[ChatMessageResponse]
