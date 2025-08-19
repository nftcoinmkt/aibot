from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import uuid
import asyncio

from src.backend.auth.schemas import User
from src.backend.auth.authentication_service import get_current_active_user, get_current_active_superuser
from src.backend.shared.database_manager import get_default_db, get_tenant_db
from .service import channel_service
from src.backend.ai_service.chat_service import chat_service
from src.backend.ai_service import schemas as ai_schemas
from src.backend.websocket.connection_manager import manager
from . import schemas

router = APIRouter()


@router.post("/channels", response_model=schemas.Channel)
def create_channel(
    channel: schemas.ChannelCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new channel.
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)

    try:
        db_channel = channel_service.create_channel(db, channel, current_user.id)

        # Convert to schema before closing the session
        channel_response = schemas.Channel(
            id=db_channel.id,
            name=db_channel.name,
            description=db_channel.description,
            created_by=db_channel.created_by,
            created_at=db_channel.created_at,
            updated_at=db_channel.updated_at,
            is_private=db_channel.is_private,
            max_members=db_channel.max_members
        )

        return channel_response
    finally:
        db.close()


@router.get("/channels", response_model=List[schemas.ChannelWithMembers])
def get_user_channels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get channels that the current user is a member of.
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        return channel_service.get_user_channels(db, current_user.id, skip, limit)
    finally:
        db.close()


@router.get("/channels/{channel_id}", response_model=schemas.Channel)
def get_channel(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific channel.
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        channel = channel_service.get_channel(db, channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Check if user is a member
        if not channel_service.is_user_member(db, channel_id, current_user.id):
            raise HTTPException(status_code=403, detail="Not a member of this channel")
        
        return channel
    finally:
        db.close()


@router.put("/channels/{channel_id}", response_model=schemas.Channel)
def update_channel(
    channel_id: int,
    channel_update: schemas.ChannelUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a channel (admin only).
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        # Check if user is admin of the channel
        user_role = channel_service.get_user_role_in_channel(db, channel_id, current_user.id)
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Only channel admins can update channels")
        
        updated_channel = channel_service.update_channel(db, channel_id, channel_update)
        if not updated_channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return updated_channel
    finally:
        db.close()


@router.delete("/channels/{channel_id}")
def delete_channel(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a channel (admin only).
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        # Check if user is admin of the channel
        user_role = channel_service.get_user_role_in_channel(db, channel_id, current_user.id)
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Only channel admins can delete channels")
        
        success = channel_service.delete_channel(db, channel_id)
        if not success:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        return {"message": "Channel deleted successfully"}
    finally:
        db.close()


@router.post("/channels/{channel_id}/members")
def add_member_to_channel(
    channel_id: int,
    member: schemas.ChannelMemberAdd,
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a member to a channel (admin only).
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        # Check if user is admin of the channel
        user_role = channel_service.get_user_role_in_channel(db, channel_id, current_user.id)
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Only channel admins can add members")
        
        success = channel_service.add_member_to_channel(db, channel_id, member.user_id, member.role)
        if not success:
            raise HTTPException(status_code=400, detail="User is already a member or channel not found")
        
        return {"message": "Member added successfully"}
    finally:
        db.close()


@router.delete("/channels/{channel_id}/members/{user_id}")
def remove_member_from_channel(
    channel_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove a member from a channel (admin only).
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        # Check if user is admin of the channel
        user_role = channel_service.get_user_role_in_channel(db, channel_id, current_user.id)
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Only channel admins can remove members")
        
        success = channel_service.remove_member_from_channel(db, channel_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Member not found in channel")
        
        return {"message": "Member removed successfully"}
    finally:
        db.close()


@router.get("/channels/{channel_id}/members", response_model=List[schemas.ChannelMemberWithUser])
def get_channel_members(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all members of a channel.
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        # Check if user is a member
        if not channel_service.is_user_member(db, channel_id, current_user.id):
            raise HTTPException(status_code=403, detail="Not a member of this channel")
        
        return channel_service.get_channel_members(db, channel_id)
    finally:
        db.close()


@router.get("/channels/{channel_id}/messages", response_model=List[schemas.ChannelMessage])
def get_channel_messages(
    channel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    days_back: int = Query(2, ge=1, le=30),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get recent messages from a specific channel (default: last 2 days).
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        # Check if user is a member
        if not channel_service.is_user_member(db, channel_id, current_user.id):
            raise HTTPException(status_code=403, detail="Not a member of this channel")
        
        messages = channel_service.get_channel_messages(
            db, 
            channel_id, 
            skip=skip, 
            limit=limit,
            days_back=days_back
        )
        return messages
    finally:
        db.close()


@router.get("/channels/{channel_id}/messages/all", response_model=List[schemas.ChannelMessage])
def get_all_channel_messages(
    channel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all messages from a specific channel (including archived).
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        # Check if user is a member
        if not channel_service.is_user_member(db, channel_id, current_user.id):
            raise HTTPException(status_code=403, detail="Not a member of this channel")
        
        messages = channel_service.get_all_channel_messages(
            db, 
            channel_id, 
            skip=skip, 
            limit=limit
        )
        return messages
    finally:
        db.close()


@router.post("/channels/archive")
def archive_old_messages(
    days_old: int = Query(7, ge=1, le=365),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Archive messages older than specified days (admin only).
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        archived_count = channel_service.archive_old_messages(db, days_old)
        return {"message": f"Archived {archived_count} messages older than {days_old} days"}
    finally:
        db.close()


@router.post("/channels/{channel_id}/chat")
async def send_message_to_channel(
    channel_id: int,
    message_data: ai_schemas.ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a regular text message to a channel with AI response and WebSocket broadcasting.
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)

    try:
        # Check if user is a member
        if not channel_service.is_user_member(db, channel_id, current_user.id):
            raise HTTPException(status_code=403, detail="Not a member of this channel")

        # Get the message text
        message_text = message_data.message
        if not message_text.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Process the message and get AI response
        try:
            messages = await chat_service.process_channel_message(
                user_id=current_user.id,
                tenant_name=current_user.tenant_name,
                message=message_text,
                channel_id=channel_id
            )

            # Broadcast new messages to WebSocket connections (excluding the sender to avoid duplicates)
            print(f"Broadcasting {len(messages)} regular chat messages to channel {channel_id}")
            for message in messages:
                message_dict = {
                    "id": message["id"],
                    "channel_id": message["channel_id"],
                    "user_id": message["user_id"],
                    "message": message["message"],
                    "response": message.get("response"),
                    "provider": message.get("provider"),
                    "message_type": message["message_type"],
                    "created_at": message["created_at"].isoformat() if hasattr(message["created_at"], 'isoformat') else str(message["created_at"]),
                    "file_url": None,
                    "file_name": None,
                    "file_type": None,
                    "is_archived": False
                }
                print(f"Broadcasting regular message: {message_dict['id']} - {message_dict['message'][:50]}...")
                # Only broadcast to other users, not the sender
                await manager.broadcast_new_message_exclude_user(channel_id, message_dict, current_user.id)

            return {"messages": messages}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")

    finally:
        db.close()


@router.post("/channels/{channel_id}/upload")
async def upload_file_to_channel(
    channel_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a file to a channel and trigger AI analysis.
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    
    try:
        # Check if user is a member
        if not channel_service.is_user_member(db, channel_id, current_user.id):
            raise HTTPException(status_code=403, detail="Not a member of this channel")
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads") / "channels" / str(channel_id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
        # Create file URL
        file_url = f"/uploads/channels/{channel_id}/{unique_filename}"
        
        # Determine file type and create appropriate message
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            message_text = f"🖼️ {file.filename}"
            analysis_prompt = f"Please analyze this image and describe what you see. Image: {file.filename}"
        elif file_extension == '.pdf':
            message_text = f"📄 {file.filename}"
            analysis_prompt = f"Please summarize this PDF document. Document: {file.filename}"
        else:
            message_text = f"📎 {file.filename}"
            analysis_prompt = f"I've uploaded a file: {file.filename}. Please acknowledge the upload."
        
        # Process the file upload and get AI analysis
        try:
            messages = await chat_service.process_file_upload(
                user_id=current_user.id,
                tenant_name=current_user.tenant_name,
                channel_id=channel_id,
                file_path=str(file_path),
                file_url=file_url,
                file_name=file.filename,
                message_text=message_text,
                analysis_prompt=analysis_prompt
            )

            # Broadcast new messages to WebSocket connections (excluding the sender to avoid duplicates)
            # The sender already has the messages from the API response
            print(f"Broadcasting {len(messages)} file upload messages to channel {channel_id}")
            for message in messages:
                # Handle attachment data properly
                attachment = message.get("attachment")
                message_dict = {
                    "id": message["id"],
                    "channel_id": message["channel_id"],
                    "user_id": message["user_id"],
                    "message": message["message"],
                    "response": message.get("response"),
                    "provider": message.get("provider"),
                    "message_type": message["message_type"],
                    "created_at": message["created_at"].isoformat() if hasattr(message["created_at"], 'isoformat') else str(message["created_at"]),
                    "attachment": attachment,
                    "file_url": attachment.get("file_url") if attachment else None,
                    "file_name": attachment.get("file_name") if attachment else None,
                    "file_type": attachment.get("file_type") if attachment else None,
                    "is_archived": message.get("is_archived", False)
                }
                print(f"Broadcasting file message: {message_dict['id']} - {message_dict['message'][:50]}...")
                # Only broadcast to other users, not the sender
                await manager.broadcast_new_message_exclude_user(channel_id, message_dict, current_user.id)

            return {"messages": messages}
        except Exception as e:
            # If AI analysis fails, still save the file message
            message = channel_service.create_file_message(
                db=db,
                channel_id=channel_id,
                user_id=current_user.id,
                message=message_text,
                file_url=file_url,
                file_name=file.filename,
                file_size=len(content)
            )
            
            return {
                "messages": [{
                    "id": message.id,
                    "channel_id": message.channel_id,
                    "user_id": message.user_id,
                    "message": message.message,
                    "response": None,
                    "provider": None,
                    "message_type": message.message_type,
                    "created_at": message.created_at,
                    "file_url": message.file_url,
                    "file_name": message.file_name,
                    "file_type": message.file_type
                }]
            }
    finally:
        db.close()
