from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from src.backend.auth.schemas import User
from src.backend.auth.authentication_service import get_current_active_user, get_user_from_token
from src.backend.shared.database_manager import get_default_db
from src.backend.core.settings import settings
from .chat_service import chat_service
from . import schemas

router = APIRouter()

@router.post("/chat", response_model=schemas.ChatResponse)
def chat_with_ai(
    request: schemas.ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_default_db)
):
    """
    Chat with the AI service.
    """
    response, provider = chat_service.process_chat_message(
        current_user.id, current_user.tenant_name, request.message
    )
    return {"response": response, "provider": provider}

@router.post("/channels/{channel_id}/chat", response_model=schemas.ChannelChatResponse)
def chat_in_channel(
    channel_id: int,
    request: schemas.ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_default_db)
):
    """
    Chat with AI in a specific channel. Returns both user message and AI response.
    """
    message_dicts = chat_service.process_channel_message(
        current_user.id, current_user.tenant_name, request.message, channel_id
    )

    # Convert dictionaries to schema objects
    messages = [schemas.ChatMessageResponse(**msg_dict) for msg_dict in message_dicts]

    return {"messages": messages}

@router.get("/chat/history", response_model=List[schemas.ChatHistory])
def get_chat_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_default_db)
):
    """
    Get chat history for the current user.
    """
    history = chat_service.get_chat_history(
        current_user.tenant_name, current_user.id, skip=skip, limit=limit
    )
    return history

@router.get("/chat/stats", response_model=dict)
def get_chat_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_default_db)
):
    """
    Get chat statistics for the current tenant.
    """
    stats = chat_service.get_chat_statistics(current_user.tenant_name)
    return stats






