from typing import Dict, List
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime, timezone


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self):
        # Store active connections by channel_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store user info for each connection
        self.connection_users: Dict[WebSocket, Dict] = {}
    
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
            "connected_at": datetime.now(timezone.utc)
        }
        
        # Notify others about user joining
        await self.broadcast_to_channel(channel_id, {
            "type": "user_joined",
            "user_id": user_id,
            "user_name": user_name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, exclude_websocket=websocket)
        
        # Send current online users to the new connection
        online_users = self.get_online_users(channel_id)
        await self.send_personal_message(websocket, {
            "type": "online_users",
            "users": online_users
        })
    
    async def disconnect(self, websocket: WebSocket):
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
            

            
            # Remove user info
            del self.connection_users[websocket]
            
            # Notify others about user leaving
            await self.broadcast_to_channel(channel_id, {
                "type": "user_left",
                "user_id": user_id,
                "user_name": user_name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
        except:
            # Connection might be closed
            await self.disconnect(websocket)
    
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
            await self.disconnect(connection)
    
    async def broadcast_new_message(self, channel_id: int, message_data: dict):
        """Broadcast a new message to all users in the channel."""
        await self.broadcast_to_channel(channel_id, {
            "type": "new_message",
            "message": message_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def broadcast_new_message_exclude_user(self, channel_id: int, message_data: dict, exclude_user_id: int):
        """Broadcast a new message to all users in the channel except the specified user."""
        print(f"Broadcasting message to channel {channel_id}, excluding user {exclude_user_id}")
        print(f"Active connections for channel {channel_id}: {len(self.active_connections.get(channel_id, []))}")

        if channel_id not in self.active_connections:
            print(f"No active connections for channel {channel_id}")
            return

        connections_to_remove = []
        message = {
            "type": "new_message",
            "message": message_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        broadcast_count = 0
        for connection in self.active_connections[channel_id]:
            # Skip the user who sent the message
            if connection in self.connection_users:
                user_info = self.connection_users[connection]
                if user_info["user_id"] == exclude_user_id:
                    print(f"Skipping sender user {exclude_user_id}")
                    continue

            try:
                await connection.send_text(json.dumps(message))
                broadcast_count += 1
                print(f"Broadcasted to user {self.connection_users.get(connection, {}).get('user_id', 'unknown')}")
            except Exception as e:
                print(f"Failed to send to connection: {e}")
                # Connection is closed, mark for removal
                connections_to_remove.append(connection)

        print(f"Successfully broadcasted to {broadcast_count} users")

        # Remove dead connections
        for connection in connections_to_remove:
            await self.disconnect(connection)
    

    
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
