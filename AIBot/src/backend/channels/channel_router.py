from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from src.backend.auth.schemas import User
from src.backend.auth.authentication_service import get_current_active_user, get_current_active_superuser
from src.backend.shared.database_manager import get_tenant_db
from src.backend.channels.channel_service import channel_service
from src.backend.ai_service.chat_service import chat_service
from src.backend.channels.channel_schemas import (
    Channel, ChannelCreate, ChannelUpdate, ChannelWithMembers, 
    ChannelMember, ChannelMemberAdd, ChannelMemberUpdate,
    ChannelMessage, ChannelStats, MessageType, ChannelRole
)

router = APIRouter()

@router.post("/channels", response_model=Channel)
def create_channel(
    channel_data: ChannelCreate,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Create a new chat channel (admin/superuser only).
    """
    # Use tenant-specific database
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        channel = channel_service.create_channel(
            db, 
            channel_data, 
            current_user.id
        )
        # Build response schema immediately
        return Channel(
            id=channel.id,
            name=channel.name,
            description=channel.description,
            is_private=channel.is_private,
            created_by=channel.created_by,
            is_active=channel.is_active,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
        )
    finally:
        db.close()

@router.get("/channels", response_model=List[ChannelWithMembers])
def get_channels(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of channels accessible to current user.
    """
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        channels = channel_service.get_channels(
            db,
            current_user.id,
            current_user.role.value,
            skip=skip,
            limit=limit
        )
        return channels
    finally:
        db.close()

@router.get("/channels/{channel_id}", response_model=Channel)
def get_channel(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific channel.
    """
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        channel = channel_service.get_channel(db, channel_id)
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        # Build Pydantic schema while the session is still open to avoid
        # DetachedInstanceError on response serialization
        channel_schema = Channel(
            id=channel.id,
            name=channel.name,
            description=channel.description,
            is_private=channel.is_private,
            created_by=channel.created_by,
            is_active=channel.is_active,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
        )
        return channel_schema
    finally:
        db.close()

@router.put("/channels/{channel_id}", response_model=Channel)
def update_channel(
    channel_id: int,
    channel_data: ChannelUpdate,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Update a channel (admin/superuser only).
    """
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        channel = channel_service.update_channel(
            db, 
            channel_id, 
            channel_data
        )
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")
        return Channel(
            id=channel.id,
            name=channel.name,
            description=channel.description,
            is_private=channel.is_private,
            created_by=channel.created_by,
            is_active=channel.is_active,
            created_at=channel.created_at,
            updated_at=channel.updated_at,
        )
    finally:
        db.close()

@router.delete("/channels/{channel_id}")
def delete_channel(
    channel_id: int,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Delete a channel (admin/superuser only).
    """
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        success = channel_service.delete_channel(db, channel_id)
        if not success:
            raise HTTPException(status_code=404, detail="Channel not found")
        return {"message": "Channel deleted successfully"}
    finally:
        db.close()

@router.post("/channels/{channel_id}/members")
def add_channel_member(
    channel_id: int,
    member_data: ChannelMemberAdd,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Add a member to a channel (admin/superuser only).
    """
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        success = channel_service.add_member(
            db,
            channel_id,
            member_data.user_id,
            member_data.role.value
        )
        if not success:
            raise HTTPException(
                status_code=400, 
                detail="User is already a member or channel not found"
            )
        return {"message": "Member added successfully"}
    finally:
        db.close()

@router.get("/channels/{channel_id}/members", response_model=List[ChannelMember])
def get_channel_members(
    channel_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all members of a channel (admin/superuser only).
    """
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        members = channel_service.get_channel_members(db, channel_id)
        return members
    finally:
        db.close()

@router.put("/channels/{channel_id}/members/{user_id}")
def update_member_role(
    channel_id: int,
    user_id: int,
    member_data: ChannelMemberUpdate,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Update a member's role in a channel (admin/superuser only).
    """
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        success = channel_service.update_member_role(
            db,
            channel_id,
            user_id,
            member_data.role.value
        )
        if not success:
            raise HTTPException(status_code=404, detail="Member not found in channel")
        return {"message": "Member role updated successfully"}
    finally:
        db.close()

@router.delete("/channels/{channel_id}/members/{user_id}")
def remove_channel_member(
    channel_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Remove a member from a channel (admin/superuser only).
    """
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        success = channel_service.remove_member(db, channel_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Member not found in channel")
        return {"message": "Member removed successfully"}
    finally:
        db.close()

@router.get("/channels/{channel_id}/messages", response_model=List[ChannelMessage])
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

@router.get("/channels/{channel_id}/messages/all", response_model=List[ChannelMessage])
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

@router.post("/channels/{channel_id}/upload")
async def upload_file_to_channel(
    channel_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a file to a channel and trigger AI analysis.
    """
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

        return {"messages": messages}
    except Exception as e:
        # If AI analysis fails, still save the file message
        db_generator = get_tenant_db(current_user.tenant_name)
        db = next(db_generator)
        try:
            message = channel_service.create_file_message(
                db=db,
                channel_id=channel_id,
                user_id=current_user.id,
                message=message_text,
                file_url=file_url,
                file_name=file.filename,
                file_size=len(content)
            )
        finally:
            db.close()

        return {
            "messages": [{
                "id": message.id,
                "channel_id": message.channel_id,
                "user_id": message.user_id,
                "message": message.message,
                "response": None,
                "provider": None,
                "message_type": message.message_type,
                "created_at": message.created_at
            }]
        }

@router.get("/channels/stats", response_model=ChannelStats)
def get_channel_stats(
    current_user: User = Depends(get_current_active_superuser)
):
    """
    Get channel statistics (admin/superuser only).
    """
    db_generator = get_tenant_db(current_user.tenant_name)
    db = next(db_generator)
    try:
        stats = channel_service.get_channel_stats(db)
        return stats
    finally:
        db.close()
