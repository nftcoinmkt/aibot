from typing import Tuple, List
import os
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.backend.core.settings import settings
from src.backend.shared.database_manager import get_tenant_db
from .models import ChatMessage
from src.backend.channels.channel_models import ChannelMessage
from .chat_agent import ChatAgent

# Import WebSocket manager for real-time updates
try:
    from src.backend.websocket.connection_manager import manager
except ImportError:
    manager = None


class ChatService:
    """Service for handling AI chat operations."""
    
    def __init__(self):
        self.chat_agent = ChatAgent()


    def save_chat_message(
        self, 
        tenant_name: str, 
        user_id: int, 
        message: str, 
        response: str, 
        provider: str,
        channel_id: int = None
    ) -> ChatMessage:
        """Save chat message to tenant-specific database."""
        # Get tenant-specific database session
        db_generator = get_tenant_db(tenant_name)
        db = next(db_generator)
        
        try:
            if channel_id:
                # Save as channel message
                chat_message = ChannelMessage(
                    channel_id=channel_id,
                    user_id=user_id,
                    message=message,
                    response=response,
                    provider=provider,
                    message_type="ai" if response else "user",
                    created_at=datetime.now(timezone.utc)
                )
            else:
                # Save as direct message
                chat_message = ChatMessage(
                    user_id=user_id,
                    message=message,
                    response=response,
                    provider=provider,
                    created_at=datetime.now(timezone.utc)
                )
            
            db.add(chat_message)
            db.commit()
            db.refresh(chat_message)
            return chat_message
        finally:
            db.close()

    def process_chat_message(
        self, 
        user_id: int, 
        tenant_name: str, 
        message: str,
        channel_id: int = None
    ) -> Tuple[str, str]:
        """Process chat message and save to history."""
        response = self.chat_agent.generate_response(message, user_id, tenant_name, channel_id)
        provider = self.chat_agent.get_current_provider()
        
        # Save to tenant-specific database
        self.save_chat_message(tenant_name, user_id, message, response, provider, channel_id)
        
        return response, provider

    async def process_channel_message(
        self,
        user_id: int,
        tenant_name: str,
        message: str,
        channel_id: int
    ) -> List[dict]:
        """Process channel message and return messages to the client.
        If AI chat is disabled, only the user message is saved and returned.
        """

        # Get tenant-specific database session
        db_generator = get_tenant_db(tenant_name)
        db = next(db_generator)

        try:
            # Save user message
            user_message = ChannelMessage(
                channel_id=channel_id,
                user_id=user_id,
                message=message,
                message_type="user",
                created_at=datetime.now(timezone.utc)
            )
            db.add(user_message)
            db.commit()
            db.refresh(user_message)

            # If AI chat is disabled, return only the user message
            if not settings.AI_CHAT_ENABLED:
                messages = [
                    {
                        "id": user_message.id,
                        "channel_id": user_message.channel_id,
                        "user_id": user_message.user_id,
                        "message": user_message.message,
                        "response": None,
                        "provider": None,
                        "message_type": user_message.message_type,
                        "created_at": user_message.created_at
                    }
                ]
            else:
                # Get AI response
                response = self.chat_agent.generate_response(message, user_id, tenant_name, channel_id)
                provider = self.chat_agent.get_current_provider()

                # Save AI response
                ai_message = ChannelMessage(
                    channel_id=channel_id,
                    user_id=-1,  # AI user ID (Flutter expects -1 for AI messages)
                    message=response,
                    response=None,  # Don't duplicate the message in response field
                    provider=provider,
                    message_type="ai",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(ai_message)
                db.commit()
                db.refresh(ai_message)

                # Convert to response format before closing the session
                messages = [
                    {
                        "id": user_message.id,
                        "channel_id": user_message.channel_id,
                        "user_id": user_message.user_id,
                        "message": user_message.message,
                        "response": None,
                        "provider": None,
                        "message_type": user_message.message_type,
                        "created_at": user_message.created_at
                    },
                    {
                        "id": ai_message.id,
                        "channel_id": ai_message.channel_id,
                        "user_id": ai_message.user_id,
                        "message": ai_message.message,
                        "response": None,  # AI messages don't need response field
                        "provider": ai_message.provider,
                        "message_type": ai_message.message_type,
                        "created_at": ai_message.created_at
                    }
                ]

            # Broadcast messages to WebSocket connections if manager is available
            # Exclude the sender to avoid duplicates (sender gets messages from API response)
            if manager:
                print(f"Broadcasting {len(messages)} messages to channel {channel_id} via WebSocket")
                for message_dict in messages:
                    preview = message_dict['message'][:50] if isinstance(message_dict.get('message'), str) else ''
                    print(f"Broadcasting message: {message_dict['id']} - {preview}...")
                    await manager.broadcast_new_message_exclude_user(channel_id, message_dict, user_id)
            else:
                print("WebSocket manager not available for broadcasting")

            return messages
        finally:
            db.close()

    def get_chat_history(
        self, 
        tenant_name: str, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get chat history for a user from tenant-specific database."""
        db_generator = get_tenant_db(tenant_name)
        db = next(db_generator)
        
        try:
            return db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id
            ).order_by(ChatMessage.created_at.desc()).offset(skip).limit(limit).all()
        finally:
            db.close()

    def get_chat_statistics(self, tenant_name: str) -> dict:
        """Get chat statistics for a tenant."""
        db_generator = get_tenant_db(tenant_name)
        db = next(db_generator)
        
        try:
            total_messages = db.query(ChatMessage).count()
            unique_users = db.query(ChatMessage.user_id).distinct().count()
            
            # Messages by provider
            groq_count = db.query(ChatMessage).filter(ChatMessage.provider == 'groq').count()
            gemini_count = db.query(ChatMessage).filter(ChatMessage.provider == 'gemini').count()
            
            return {
                "total_messages": total_messages,
                "unique_users": unique_users,
                "messages_by_provider": {
                    "groq": groq_count,
                    "gemini": gemini_count
                }
            }
        finally:
            db.close()

   

    async def process_file_upload(
        self,
        user_id: int,
        tenant_name: str,
        channel_id: int,
        file_path: str,
        file_url: str,
        file_name: str,
        message_text: str,
        analysis_prompt: str
    ) -> List[dict]:
        """Process file upload and generate AI analysis."""
        # Get tenant-specific database session
        db_generator = get_tenant_db(tenant_name)
        db = next(db_generator)

        try:
            # Save user message with file
            file_extension = file_name.split('.')[-1].lower() if '.' in file_name else ''
            user_message = ChannelMessage(
                channel_id=channel_id,
                user_id=user_id,
                message=message_text,
                message_type="user",
                created_at=datetime.now(timezone.utc),
                file_url=file_url,
                file_name=file_name,
                file_type=file_extension
            )
            db.add(user_message)
            db.commit()
            db.refresh(user_message)

            # If AI chat is disabled, skip AI analysis and only return the user message
            if not settings.AI_CHAT_ENABLED:
                messages = [
                    {
                        "id": user_message.id,
                        "channel_id": user_message.channel_id,
                        "user_id": user_message.user_id,
                        "message": user_message.message,
                        "response": None,
                        "provider": None,
                        "message_type": user_message.message_type,
                        "created_at": user_message.created_at,
                        "attachment": {
                            "id": str(user_message.id),
                            "file_url": user_message.file_url,
                            "file_name": user_message.file_name,
                            "file_type": user_message.file_type
                        } if user_message.file_url else None
                    }
                ]
            else:
                # Get AI analysis of the file
                try:
                    ai_response = self.chat_agent.analyze_file(file_path, analysis_prompt, user_id, tenant_name, channel_id)
                    provider = self.chat_agent.get_current_provider()
                except Exception as e:
                    print(f"AI analysis failed: {str(e)}")
                    ai_response = f"File uploaded successfully! I can see you've shared {file_name}. Unfortunately, I encountered an issue analyzing it: {str(e)}"
                    provider = self.chat_agent.get_current_provider()

                # Save AI response
                ai_message = ChannelMessage(
                    channel_id=channel_id,
                    user_id=-1,  # AI user ID
                    message=ai_response,
                    response=None,  # Don't duplicate the message in response field
                    provider=provider,
                    message_type="ai",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(ai_message)
                db.commit()
                db.refresh(ai_message)

                # Convert to response format before closing the session
                messages = [
                    {
                        "id": user_message.id,
                        "channel_id": user_message.channel_id,
                        "user_id": user_message.user_id,
                        "message": user_message.message,
                        "response": None,
                        "provider": None,
                        "message_type": user_message.message_type,
                        "created_at": user_message.created_at,
                        "attachment": {
                            "id": str(user_message.id),
                            "file_url": user_message.file_url,
                            "file_name": user_message.file_name,
                            "file_type": user_message.file_type
                        } if user_message.file_url else None
                    },
                    {
                        "id": ai_message.id,
                        "channel_id": ai_message.channel_id,
                        "user_id": ai_message.user_id,
                        "message": ai_message.message,
                        "response": None,  # AI messages don't need response field
                        "provider": ai_message.provider,
                        "message_type": ai_message.message_type,
                        "created_at": ai_message.created_at,
                        "attachment": None
                    }
                ]

            # Broadcast messages to WebSocket connections if manager is available
            # Exclude the sender to avoid duplicates (sender gets messages from API response)
            if manager:
                print(f"Broadcasting {len(messages)} uploaded-file messages to channel {channel_id} via WebSocket")
                for message_dict in messages:
                    preview = message_dict['message'][:50] if isinstance(message_dict.get('message'), str) else ''
                    print(f"Broadcasting message: {message_dict['id']} - {preview}...")
                    await manager.broadcast_new_message_exclude_user(channel_id, message_dict, user_id)
            else:
                print("WebSocket manager not available for broadcasting uploaded messages")

            return messages
        finally:
            db.close()


# Global chat service instance
chat_service = ChatService()
