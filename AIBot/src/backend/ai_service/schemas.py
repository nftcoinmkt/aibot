
from pydantic import BaseModel
from datetime import datetime
from typing import List

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
