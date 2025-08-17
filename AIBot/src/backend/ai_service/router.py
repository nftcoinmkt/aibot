from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import json
from urllib.parse import parse_qs
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

@router.post("/channels/{channel_id}/chat", response_model=schemas.ChatResponse)
def chat_in_channel(
    channel_id: int,
    request: schemas.ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_default_db)
):
    """
    Chat with AI in a specific channel.
    """
    response, provider = chat_service.process_chat_message(
        current_user.id, current_user.tenant_name, request.message, channel_id
    )
    return {"response": response, "provider": provider}

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

async def get_user_from_websocket_token(websocket: WebSocket) -> User:
    """Extract and validate user from WebSocket token."""
    try:
        # Get token from query parameters
        query_params = parse_qs(websocket.url.query)
        token = query_params.get("token", [None])[0]
        
        if not token:
            await websocket.close(code=4001, reason="Missing authentication token")
            return None
            
        # Decode and validate token
        user = get_user_from_token(token)
        if not user:
            await websocket.close(code=4001, reason="Invalid authentication token")
            return None
            
        return user
    except Exception as e:
        await websocket.close(code=4001, reason=f"Authentication error: {str(e)}")
        return None

@router.websocket("/chat/stream")
async def websocket_chat_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat responses.
    Connect with: ws://localhost:8000/api/v1/chat/stream?token=YOUR_JWT_TOKEN
    """
    await websocket.accept()
    
    # Authenticate user
    user = await get_user_from_websocket_token(websocket)
    if not user:
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = message_data.get("message", "")
            channel_id = message_data.get("channel_id")
            
            if not message:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "Message cannot be empty"
                }))
                continue
            
            # Send typing indicator
            await websocket.send_text(json.dumps({
                "type": "typing",
                "content": "AI is typing..."
            }))
            
            # Stream response
            full_response = ""
            async for chunk in chat_service.stream_chat_response(
                user.id, user.tenant_name, message, channel_id
            ):
                full_response += chunk
                await websocket.send_text(json.dumps({
                    "type": "chunk",
                    "content": chunk
                }))
            
            # Send complete message in expected format for frontend
            await websocket.send_text(json.dumps({
                "id": int(datetime.now().timestamp() * 1000),
                "channelId": channel_id,
                "userId": 0,  # AI user ID
                "message": full_response,
                "timestamp": datetime.now().isoformat(),
                "response": full_response,
                "provider": "ai"
            }))
            
            # Send completion signal
            await websocket.send_text(json.dumps({
                "type": "complete",
                "content": "Response complete"
            }))
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user.email}")
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": f"Error: {str(e)}"
        }))

@router.websocket("/channels/{channel_id}/stream")
async def websocket_channel_stream(websocket: WebSocket, channel_id: int):
    """
    WebSocket endpoint for streaming chat responses in a specific channel.
    Connect with: ws://localhost:8000/api/v1/channels/{channel_id}/stream?token=YOUR_JWT_TOKEN
    """
    await websocket.accept()
    
    # Authenticate user
    user = await get_user_from_websocket_token(websocket)
    if not user:
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = message_data.get("message", "")
            
            if not message:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": "Message cannot be empty"
                }))
                continue
            
            # Send typing indicator
            await websocket.send_text(json.dumps({
                "type": "typing",
                "content": "AI is typing..."
            }))
            
            # Stream response with channel_id
            full_response = ""
            async for chunk in chat_service.stream_chat_response(
                user.id, user.tenant_name, message, channel_id
            ):
                full_response += chunk
                await websocket.send_text(json.dumps({
                    "type": "chunk",
                    "content": chunk,
                    "channel_id": channel_id
                }))
            
            # Send complete message in expected format for frontend
            await websocket.send_text(json.dumps({
                "id": int(datetime.now().timestamp() * 1000),
                "channelId": channel_id,
                "userId": 0,  # AI user ID
                "message": full_response,
                "timestamp": datetime.now().isoformat(),
                "response": full_response,
                "provider": "ai"
            }))
            
            # Send completion signal
            await websocket.send_text(json.dumps({
                "type": "complete",
                "content": "Response complete",
                "channel_id": channel_id
            }))
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user {user.email} in channel {channel_id}")
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": f"Error: {str(e)}",
            "channel_id": channel_id
        }))
