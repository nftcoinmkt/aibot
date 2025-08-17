from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from src.backend.shared.database_manager import Base

# Association table for channel members
channel_members = Table(
    'channel_members',
    Base.metadata,
    Column('channel_id', Integer, ForeignKey('channels.id'), primary_key=True),
    Column('user_id', Integer, primary_key=True),  # Reference to user in main DB
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('role', String, default='member')  # 'admin', 'moderator', 'member'
)


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=False)  # Reference to user in main DB
    is_private = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to chat messages
    messages = relationship("ChannelMessage", back_populates="channel", cascade="all, delete-orphan")


class ChannelMessage(Base):
    __tablename__ = "channel_messages"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    user_id = Column(Integer, nullable=False)  # Reference to user in main DB
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)  # AI response if applicable
    provider = Column(String, nullable=True)  # 'groq' or 'gemini' for AI responses
    message_type = Column(String, default='user')  # 'user', 'ai', 'system'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional metadata
    message_length = Column(Integer, nullable=True)
    response_length = Column(Integer, nullable=True)
    processing_time = Column(String, nullable=True)
    
    # Relationship
    channel = relationship("Channel", back_populates="messages")
