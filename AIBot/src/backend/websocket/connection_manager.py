from typing import Dict, List, Set
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        # Store active connections by channel_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store user info for each connection
        self.connection_users: Dict[WebSocket, Dict] = {}
        # Store typing users by channel
        self.typing_users: Dict[int, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, channel_id: int, user_id: int, user_name: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Add to channel connections
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = []
        self.active_connections[channel_id].append(websocket)
        
        # Store user info
        self.connection_users[websocket] = {
            "user_id": user_id,
            "user_name": user_name,
            "channel_id": channel_id,
            "connected_at": datetime.utcnow()
        }
        
        # Notify others about user joining
        await self.broadcast_to_channel(channel_id, {
            "type": "user_joined",
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_websocket=websocket)
        
        # Send current online users to the new connection
        online_users = self.get_online_users(channel_id)
        await self.send_personal_message(websocket, {
            "type": "online_users",
            "users": online_users
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.connection_users:
            user_info = self.connection_users[websocket]
            channel_id = user_info["channel_id"]
            user_id = user_info["user_id"]
            user_name = user_info["user_name"]
            
            # Remove from connections
            if channel_id in self.active_connections:
                if websocket in self.active_connections[channel_id]:
                    self.active_connections[channel_id].remove(websocket)
                
                # Clean up empty channel
                if not self.active_connections[channel_id]:
                    del self.active_connections[channel_id]
            
            # Remove from typing users
            if channel_id in self.typing_users:
                self.typing_users[channel_id].discard(user_id)
                if not self.typing_users[channel_id]:
                    del self.typing_users[channel_id]
            
            # Remove user info
            del self.connection_users[websocket]
            
            # Notify others about user leaving
            asyncio.create_task(self.broadcast_to_channel(channel_id, {
                "type": "user_left",
                "user_id": user_id,
                "user_name": user_name,
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except:
            # Connection might be closed
            self.disconnect(websocket)
    
    async def broadcast_to_channel(self, channel_id: int, message: dict, exclude_websocket: WebSocket = None):
        """Broadcast a message to all connections in a channel."""
        if channel_id not in self.active_connections:
            return
        
        connections_to_remove = []
        for connection in self.active_connections[channel_id]:
            if connection == exclude_websocket:
                continue
            
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Connection is closed, mark for removal
                connections_to_remove.append(connection)
        
        # Remove dead connections
        for connection in connections_to_remove:
            self.disconnect(connection)
    
    async def broadcast_new_message(self, channel_id: int, message_data: dict):
        """Broadcast a new message to all users in the channel."""
        await self.broadcast_to_channel(channel_id, {
            "type": "new_message",
            "message": message_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_typing_status(self, channel_id: int, user_id: int, user_name: str, is_typing: bool):
        """Broadcast typing status to channel users."""
        if channel_id not in self.typing_users:
            self.typing_users[channel_id] = set()
        
        if is_typing:
            self.typing_users[channel_id].add(user_id)
        else:
            self.typing_users[channel_id].discard(user_id)
        
        await self.broadcast_to_channel(channel_id, {
            "type": "typing_status",
            "user_id": user_id,
            "user_name": user_name,
            "is_typing": is_typing,
            "typing_users": list(self.typing_users[channel_id]),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_online_users(self, channel_id: int) -> List[dict]:
        """Get list of online users in a channel."""
        if channel_id not in self.active_connections:
            return []
        
        online_users = []
        for connection in self.active_connections[channel_id]:
            if connection in self.connection_users:
                user_info = self.connection_users[connection]
                online_users.append({
                    "user_id": user_info["user_id"],
                    "user_name": user_info["user_name"],
                    "connected_at": user_info["connected_at"].isoformat()
                })
        
        return online_users
    
    def get_channel_connection_count(self, channel_id: int) -> int:
        """Get number of active connections in a channel."""
        return len(self.active_connections.get(channel_id, []))


# Global connection manager instance
manager = ConnectionManager()
