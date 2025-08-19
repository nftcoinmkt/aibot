from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.security import HTTPBearer
import json
from typing import Optional

from src.backend.auth.websocket_auth import get_current_user_from_token
from src.backend.auth.schemas import User
from .connection_manager import manager

router = APIRouter()
security = HTTPBearer()


@router.websocket("/ws/channels/{channel_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel_id: int,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time chat in a channel.
    """
    try:
        # Authenticate user from token
        user = await get_current_user_from_token(token)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Connect to channel
        await manager.connect(websocket, channel_id, user.id, user.email)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                message_type = message_data.get("type")
                
                if message_type == "ping":
                    # Handle ping/keepalive
                    await manager.send_personal_message(websocket, {
                        "type": "pong",
                        "timestamp": message_data.get("timestamp")
                    })
                
                elif message_type == "message_read":
                    # Handle message read status
                    message_id = message_data.get("message_id")
                    await manager.broadcast_to_channel(channel_id, {
                        "type": "message_read",
                        "message_id": message_id,
                        "user_id": user.id,
                        "user_name": user.email
                    }, exclude_websocket=websocket)
        
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"WebSocket error for user {user.id} in channel {channel_id}: {e}")
        
    except Exception as e:
        print(f"WebSocket authentication error: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
    
    finally:
        # Clean up connection
        await manager.disconnect(websocket)


@router.websocket("/ws/channels/{channel_id}/simple")
async def simple_websocket_endpoint(
    websocket: WebSocket,
    channel_id: int,
    user_id: int = Query(...),
    user_name: str = Query(...),
):
    """
    Simple WebSocket endpoint without authentication (for testing).
    """
    try:
        await manager.connect(websocket, channel_id, user_id, user_name)
        
        try:
            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                message_type = message_data.get("type")
                
                if message_type == "ping":
                    await manager.send_personal_message(websocket, {
                        "type": "pong",
                        "timestamp": message_data.get("timestamp")
                    })
        
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"Simple WebSocket error: {e}")
    
    finally:
        await manager.disconnect(websocket)
