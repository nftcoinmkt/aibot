from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime, timezone

from src.backend.core.settings import settings
from src.backend.shared.database_manager import get_tenant_db
from .ai_providers import GroqProvider, GeminiProvider
from .models import ChatMessage


class ChatState(TypedDict):
    """State for chat processing workflow."""
    message: str
    response: str
    user_id: int
    tenant_name: str
    channel_id: Optional[int]
    conversation_history: List[Dict[str, str]]


class ChatAgent:
    """AI Chat Agent responsible for state management, workflow, and LLM logic."""
    
    def __init__(self):
        """Initialize ChatAgent with AI providers and workflow."""
        self.groq_provider = GroqProvider()
        self.gemini_provider = GeminiProvider()
        self.workflow = self._create_workflow()
        self.memory_limit = 10  # Number of previous messages to remember
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for chat processing."""
        workflow = StateGraph(ChatState)
        workflow.add_node("retrieve_memory", self._retrieve_memory)
        workflow.add_node("process_message", self._process_message)
        workflow.set_entry_point("retrieve_memory")
        workflow.add_edge("retrieve_memory", "process_message")
        workflow.add_edge("process_message", END)
        return workflow.compile()
    
    def _retrieve_memory(self, state: ChatState) -> ChatState:
        """Retrieve conversation history from long-term memory."""
        conversation_history = self._get_conversation_history(
            state['tenant_name'], 
            state.get('channel_id')
        )
        
        return {
            **state,
            "conversation_history": conversation_history
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _process_message(self, state: ChatState) -> ChatState:
        """Process chat message using configured AI provider with memory context."""
        message = state['message']
        conversation_history = state.get('conversation_history', [])
        
        # Build context with conversation history
        context_message = self._build_context_message(message, conversation_history)
        
        try:
            if settings.AI_PROVIDER == 'groq':
                response = self.groq_provider.generate_response(context_message)
            elif settings.AI_PROVIDER == 'gemini':
                response = self.gemini_provider.generate_response(context_message)
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
    
    def _get_conversation_history(self, tenant_name: str, channel_id: Optional[int] = None) -> List[Dict[str, str]]:
        """Retrieve conversation history from current day based on channel_id."""
        if not channel_id:
            return []
            
        db_generator = get_tenant_db(tenant_name)
        db = next(db_generator)
        
        try:
            from src.backend.channels.channel_models import ChannelMessage
            
            # Get start of current day in UTC
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            recent_messages = db.query(ChannelMessage).filter(
                ChannelMessage.channel_id == channel_id,
                ChannelMessage.created_at >= today_start
            ).order_by(
                ChannelMessage.created_at.desc()
            ).all()
            
            # Convert to conversation format (reverse to get chronological order)
            conversation_history = []
            for msg in reversed(recent_messages):
                if msg.message_type == "user":
                    conversation_history.append({"role": "user", "content": msg.message})
                elif msg.message_type == "ai":
                    conversation_history.append({"role": "assistant", "content": msg.message})
            
            return conversation_history
        finally:
            db.close()
    
    def _build_context_message(self, current_message: str, conversation_history: List[Dict[str, str]]) -> str:
        """Build context message with conversation history."""
        if not conversation_history:
            return current_message
        
        context_parts = ["Previous conversation context:"]
        
        # Add recent conversation history
        for entry in conversation_history:#[-20:]:  # Last 3 exchanges (6 messages)
            role = "User" if entry["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {entry['content']}")
        
        context_parts.extend([
            "\nCurrent message:",
            f"User: {current_message}"
        ])
        
        return "\n".join(context_parts)
    
    def generate_response(self, message: str, user_id: int, tenant_name: str, channel_id: Optional[int] = None) -> str:
        """Generate AI response for a given message with memory context."""
        inputs = {
            "message": message,
            "user_id": user_id,
            "tenant_name": tenant_name,
            "channel_id": channel_id,
            "conversation_history": []
        }
        
        result = self.workflow.invoke(inputs)
        return result['response']
    
    def analyze_file(self, file_path: str, analysis_prompt: str, user_id: int = None, tenant_name: str = None, channel_id: Optional[int] = None) -> str:
        """Analyze a file using the configured AI provider with optional memory context."""
        try:
            # Build context with memory if channel info provided
            context_prompt = analysis_prompt
            if tenant_name and channel_id:
                conversation_history = self._get_conversation_history(tenant_name, channel_id)
                if conversation_history:
                    context_prompt = self._build_context_message(analysis_prompt, conversation_history)
            
            if settings.AI_PROVIDER == 'groq':
                return self.groq_provider.analyze_file(file_path, context_prompt)
            elif settings.AI_PROVIDER == 'gemini':
                return self.gemini_provider.analyze_file(file_path, context_prompt)
            else:
                return "File uploaded successfully, but AI analysis is not available."
        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")
    
    def get_current_provider(self) -> str:
        """Get the current AI provider name."""
        return settings.AI_PROVIDER
    
    def clear_memory(self, tenant_name: str, channel_id: int) -> bool:
        """Clear conversation memory for a specific channel."""
        db_generator = get_tenant_db(tenant_name)
        db = next(db_generator)
        
        try:
            from src.backend.channels.channel_models import ChannelMessage
            
            deleted_count = db.query(ChannelMessage).filter(
                ChannelMessage.channel_id == channel_id
            ).delete()
            db.commit()
            return deleted_count > 0
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to clear memory: {str(e)}")
        finally:
            db.close()
    
    def get_memory_stats(self, tenant_name: str, channel_id: int) -> Dict[str, int]:
        """Get memory statistics for a channel."""
        db_generator = get_tenant_db(tenant_name)
        db = next(db_generator)
        
        try:
            from src.backend.channels.channel_models import ChannelMessage
            
            total_messages = db.query(ChannelMessage).filter(
                ChannelMessage.channel_id == channel_id
            ).count()
            
            recent_messages = db.query(ChannelMessage).filter(
                ChannelMessage.channel_id == channel_id
            ).order_by(
                ChannelMessage.created_at.desc()
            ).limit(self.memory_limit).count()
            
            return {
                "total_messages": total_messages,
                "recent_messages_in_memory": recent_messages,
                "memory_limit": self.memory_limit
            }
        finally:
            db.close()
