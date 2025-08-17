from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

from src.backend.shared.database_manager import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Reference to user in main DB
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    provider = Column(String, nullable=False)  # 'groq' or 'gemini'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional metadata
    message_length = Column(Integer, nullable=True)
    response_length = Column(Integer, nullable=True)
    processing_time = Column(String, nullable=True)  # Time taken to generate response
