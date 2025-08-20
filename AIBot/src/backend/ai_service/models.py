from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone

from src.backend.shared.database_manager import TenantBase


class ChatMessage(TenantBase):
    __tablename__ = "chat_messages"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Reference to user in main DB
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    provider = Column(String, nullable=False)  # 'groq' or 'gemini'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Additional metadata
    message_length = Column(Integer, nullable=True)
    response_length = Column(Integer, nullable=True)
    processing_time = Column(String, nullable=True)  # Time taken to generate response
