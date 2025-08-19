from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from src.backend.shared.database_manager import get_tenant_db
from .models import Channel, ChannelMessage, channel_members
from . import schemas
from src.backend.auth.schemas import UserRole


class ChannelService:
    """Service for managing channels and channel messages."""

    def create_channel(
        self, db: Session, channel: schemas.ChannelCreate, created_by: int
    ) -> Channel:
        """Create a new channel."""
        db_channel = Channel(
            name=channel.name,
            description=channel.description,
            created_by=created_by,
            is_private=channel.is_private,
            max_members=channel.max_members,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_channel)
        db.commit()
        db.refresh(db_channel)

        # Add creator as admin member
        self.add_member_to_channel(db, db_channel.id, created_by, "admin")

        # Ensure the object is still attached to the session before returning
        db.refresh(db_channel)

        return db_channel

    def get_channel(self, db: Session, channel_id: int) -> Optional[Channel]:
        """Get a channel by ID."""
        return db.query(Channel).filter(Channel.id == channel_id).first()

    def get_channels(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[Channel]:
        """Get all channels."""
        return db.query(Channel).offset(skip).limit(limit).all()

    def get_user_channels(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[schemas.ChannelWithMembers]:
        """Get channels that a user is a member of."""
        channels = (
            db.query(Channel)
            .join(channel_members)
            .filter(channel_members.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Add member count to each channel
        result = []
        for channel in channels:
            member_count = (
                db.query(func.count(channel_members.c.user_id))
                .filter(channel_members.c.channel_id == channel.id)
                .scalar()
            )
            
            channel_with_members = schemas.ChannelWithMembers(
                id=channel.id,
                name=channel.name,
                description=channel.description,
                created_by=channel.created_by,
                created_at=channel.created_at,
                updated_at=channel.updated_at,
                is_private=channel.is_private,
                max_members=channel.max_members,
                member_count=member_count
            )
            result.append(channel_with_members)
        
        return result

    def update_channel(
        self, db: Session, channel_id: int, channel_update: schemas.ChannelUpdate
    ) -> Optional[Channel]:
        """Update a channel."""
        db_channel = self.get_channel(db, channel_id)
        if not db_channel:
            return None
        
        update_data = channel_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_channel, field, value)
        
        db_channel.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_channel)
        return db_channel

    def delete_channel(self, db: Session, channel_id: int) -> bool:
        """Delete a channel."""
        db_channel = self.get_channel(db, channel_id)
        if not db_channel:
            return False
        
        db.delete(db_channel)
        db.commit()
        return True

    def add_member_to_channel(
        self, db: Session, channel_id: int, user_id: int, role: str = "member"
    ) -> bool:
        """Add a member to a channel."""
        # Check if user is already a member
        existing = (
            db.query(channel_members)
            .filter(
                and_(
                    channel_members.c.channel_id == channel_id,
                    channel_members.c.user_id == user_id
                )
            )
            .first()
        )
        
        if existing:
            return False  # User already a member
        
        # Add new member
        stmt = channel_members.insert().values(
            channel_id=channel_id,
            user_id=user_id,
            role=role,
            joined_at=datetime.utcnow()
        )
        db.execute(stmt)
        db.commit()
        return True

    def remove_member_from_channel(
        self, db: Session, channel_id: int, user_id: int
    ) -> bool:
        """Remove a member from a channel."""
        stmt = channel_members.delete().where(
            and_(
                channel_members.c.channel_id == channel_id,
                channel_members.c.user_id == user_id
            )
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount > 0

    def get_channel_members(
        self, db: Session, channel_id: int
    ) -> List[schemas.ChannelMemberWithUser]:
        """Get all members of a channel with user information."""
        from src.backend.auth.models import User

        # Join channel_members with users table to get user information
        members_with_users = (
            db.query(
                channel_members.c.user_id,
                channel_members.c.role,
                channel_members.c.joined_at,
                User.full_name,
                User.email
            )
            .join(User, channel_members.c.user_id == User.id)
            .filter(channel_members.c.channel_id == channel_id)
            .all()
        )

        return [
            schemas.ChannelMemberWithUser(
                user_id=member.user_id,
                role=member.role,
                joined_at=member.joined_at,
                user_full_name=member.full_name,
                user_email=member.email
            )
            for member in members_with_users
        ]

    def is_user_member(self, db: Session, channel_id: int, user_id: int) -> bool:
        """Check if a user is a member of a channel."""
        member = (
            db.query(channel_members)
            .filter(
                and_(
                    channel_members.c.channel_id == channel_id,
                    channel_members.c.user_id == user_id
                )
            )
            .first()
        )
        return member is not None

    def get_user_role_in_channel(
        self, db: Session, channel_id: int, user_id: int
    ) -> Optional[str]:
        """Get user's role in a channel."""
        member = (
            db.query(channel_members)
            .filter(
                and_(
                    channel_members.c.channel_id == channel_id,
                    channel_members.c.user_id == user_id
                )
            )
            .first()
        )
        return member.role if member else None

    def get_channel_messages(
        self, db: Session, channel_id: int, skip: int = 0, limit: int = 50, days_back: int = 2
    ) -> List[schemas.ChannelMessage]:
        """Get recent messages from a specific channel (default: last 2 days)."""
        # Calculate the cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        messages = (
            db.query(ChannelMessage)
            .filter(
                and_(
                    ChannelMessage.channel_id == channel_id,
                    ChannelMessage.is_archived == False,
                    ChannelMessage.created_at >= cutoff_date
                )
            )
            .order_by(ChannelMessage.created_at.asc())  # Changed to ascending for chronological order
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [
            schemas.ChannelMessage(
                id=msg.id,
                channel_id=msg.channel_id,
                user_id=msg.user_id,
                message=msg.message,
                response=msg.response,
                provider=msg.provider,
                message_type=msg.message_type,
                created_at=msg.created_at,
                file_url=msg.file_url,
                file_name=msg.file_name,
                file_type=msg.file_type,
                is_archived=msg.is_archived
            )
            for msg in messages
        ]

    def get_all_channel_messages(
        self, db: Session, channel_id: int, skip: int = 0, limit: int = 50
    ) -> List[schemas.ChannelMessage]:
        """Get all messages from a specific channel (including archived)."""
        messages = (
            db.query(ChannelMessage)
            .filter(ChannelMessage.channel_id == channel_id)
            .order_by(ChannelMessage.created_at.asc())  # Changed to ascending for chronological order
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return [
            schemas.ChannelMessage(
                id=msg.id,
                channel_id=msg.channel_id,
                user_id=msg.user_id,
                message=msg.message,
                response=msg.response,
                provider=msg.provider,
                message_type=msg.message_type,
                created_at=msg.created_at,
                file_url=msg.file_url,
                file_name=msg.file_name,
                file_type=msg.file_type,
                is_archived=msg.is_archived
            )
            for msg in messages
        ]

    def create_file_message(
        self, 
        db: Session, 
        channel_id: int, 
        user_id: int, 
        message: str,
        file_url: str,
        file_name: str,
        file_size: int
    ) -> ChannelMessage:
        """Create a message with file attachment."""
        # Determine file type from extension
        file_extension = file_name.split('.')[-1].lower() if '.' in file_name else ''
        
        channel_message = ChannelMessage(
            channel_id=channel_id,
            user_id=user_id,
            message=message,
            message_type="user",
            created_at=datetime.utcnow(),
            message_length=len(message),
            file_url=file_url,
            file_name=file_name,
            file_type=file_extension
        )
        
        db.add(channel_message)
        db.commit()
        db.refresh(channel_message)
        return channel_message

    def archive_old_messages(self, db: Session, days_old: int = 7) -> int:
        """Archive messages older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Update old messages to archived status
        updated_count = (
            db.query(ChannelMessage)
            .filter(
                and_(
                    ChannelMessage.created_at < cutoff_date,
                    ChannelMessage.is_archived == False
                )
            )
            .update({"is_archived": True})
        )
        
        db.commit()
        return updated_count


# Global channel service instance
channel_service = ChannelService()
