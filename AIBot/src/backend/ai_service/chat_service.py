from langgraph.graph import StateGraph, END
from typing import TypedDict, Tuple, List, AsyncGenerator
import os
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.backend.core.settings import settings
from src.backend.shared.database_manager import get_tenant_db
from .models import ChatMessage
from src.backend.channels.channel_models import ChannelMessage
from .ai_providers import GroqProvider, GeminiProvider
from tenacity import retry, stop_after_attempt, wait_exponential

# Import WebSocket manager for real-time updates
try:
    from src.backend.websocket.connection_manager import manager
except ImportError:
    manager = None


class GraphState(TypedDict):
    message: str
    response: str
    user_id: int
    tenant_name: str


class ChatService:
    """Service for handling AI chat operations."""
    
    def __init__(self):
        self.groq_provider = GroqProvider()
        self.gemini_provider = GeminiProvider()
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for chat processing."""
        workflow = StateGraph(GraphState)
        workflow.add_node("process_message", self._process_message)
        workflow.set_entry_point("process_message")
        workflow.add_edge("process_message", END)
        return workflow.compile()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _process_message(self, state: GraphState) -> GraphState:
        """Process chat message using configured AI provider."""
        message = state['message']
        
        try:
            if settings.AI_PROVIDER == 'groq':
                response = self.groq_provider.generate_response(message)
            elif settings.AI_PROVIDER == 'gemini':
                response = self.gemini_provider.generate_response(message)
            else:
                raise ValueError(f"Invalid AI_PROVIDER: {settings.AI_PROVIDER}")
                
            return {
                **state,
                "response": response
            }
        except Exception as e:
            # Fallback response
            return {
                **state,
                "response": f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}"
            }

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
        inputs = {
            "message": message,
            "user_id": user_id,
            "tenant_name": tenant_name
        }
        
        result = self.workflow.invoke(inputs)
        response = result['response']
        provider = settings.AI_PROVIDER
        
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
        """Process channel message and return both user message and AI response as separate objects."""
        # Get AI response
        inputs = {
            "message": message,
            "user_id": user_id,
            "tenant_name": tenant_name
        }

        result = self.workflow.invoke(inputs)
        response = result['response']
        provider = settings.AI_PROVIDER

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
                    print(f"Broadcasting message: {message_dict['id']} - {message_dict['message'][:50]}...")
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

    async def stream_chat_response(
        self, 
        user_id: int, 
        tenant_name: str, 
        message: str,
        channel_id: int = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response in chunks for WebSocket."""
        try:
            # Get AI response
            if settings.AI_PROVIDER == 'groq':
                response = self.groq_provider.generate_response(message)
            elif settings.AI_PROVIDER == 'gemini':
                response = self.gemini_provider.generate_response(message)
            else:
                response = "I apologize, but I'm having trouble processing your request right now."
            
            # Stream response word by word
            words = response.split()
            streamed_response = ""
            
            for i, word in enumerate(words):
                streamed_response += word + " "
                yield word + " "
                # Small delay to simulate streaming
                await asyncio.sleep(0.1)
            
            # Save complete message to database
            self.save_chat_message(
                tenant_name, 
                user_id, 
                message, 
                streamed_response.strip(), 
                settings.AI_PROVIDER, 
                channel_id
            )
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            yield error_msg
            # Save error to database
            self.save_chat_message(
                tenant_name, 
                user_id, 
                message, 
                error_msg, 
                settings.AI_PROVIDER, 
                channel_id
            )

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

            # Get AI analysis of the file
            try:
                if settings.AI_PROVIDER == 'groq':
                    ai_response = self.groq_provider.analyze_file(file_path, analysis_prompt)
                elif settings.AI_PROVIDER == 'gemini':
                    ai_response = self.gemini_provider.analyze_file(file_path, analysis_prompt)
                else:
                    ai_response = "File uploaded successfully, but AI analysis is not available."

                provider = settings.AI_PROVIDER
            except Exception as e:
                print(f"AI analysis failed: {str(e)}")
                ai_response = f"File uploaded successfully! I can see you've shared {file_name}. Unfortunately, I encountered an issue analyzing it: {str(e)}"
                provider = settings.AI_PROVIDER

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
