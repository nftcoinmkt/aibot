from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from src.backend.shared.database_manager import get_tenant_db
from .channel_models import Channel, ChannelMessage, channel_members
from . import channel_schemas
from src.backend.auth.schemas import UserRole


class ChannelService:
    """Service for managing chat channels."""

    def create_channel(
        self, db: Session, channel_data: channel_schemas.ChannelCreate, created_by: int
    ) -> Channel:
        """Create a new channel."""
        channel = Channel(
            name=channel_data.name,
            description=channel_data.description,
            is_private=channel_data.is_private,
            created_by=created_by,
            created_at=datetime.utcnow(),
        )
        db.add(channel)
        db.commit()
        db.refresh(channel)

        # Add creator as admin member
        self._add_member_to_channel(db, channel.id, created_by, "admin")

        return channel

    def get_channels(
        self,
        db: Session,
        user_id: int,
        user_role: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[channel_schemas.ChannelWithMembers]:
        """Get channels accessible to user."""
        query = db.query(Channel).filter(Channel.is_active == True)

        # Non-admin users can only see public channels or channels they're members of
        if user_role not in [UserRole.ADMIN.value, UserRole.SUPER_USER.value]:
            member_channels = (
                db.query(channel_members.c.channel_id)
                .filter(channel_members.c.user_id == user_id)
                .subquery()
            )

            query = query.filter(
                and_(
                    Channel.is_private == False, Channel.id.in_(member_channels)
                )
            )

        channels = query.offset(skip).limit(limit).all()

        # Get member counts and user roles
        result = []
        for channel in channels:
            member_count = (
                db.query(func.count(channel_members.c.user_id))
                .filter(channel_members.c.channel_id == channel.id)
                .scalar()
            )

            user_role_in_channel = (
                db.query(channel_members.c.role)
                .filter(
                    and_(
                        channel_members.c.channel_id == channel.id,
                        channel_members.c.user_id == user_id,
                    )
                )
                .scalar()
            )

            channel_with_members = channel_schemas.ChannelWithMembers(
                **channel.__dict__,
                member_count=member_count,
                user_role=user_role_in_channel
            )
            result.append(channel_with_members)

        return result

    def get_channel(self, db: Session, channel_id: int) -> Optional[Channel]:
        """Get a specific channel."""
        return db.query(Channel).filter(Channel.id == channel_id).first()

    def update_channel(
        self, db: Session, channel_id: int, channel_data: channel_schemas.ChannelUpdate
    ) -> Optional[Channel]:
        """Update a channel."""
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            return None

        update_data = channel_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(channel, field, value)

        channel.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(channel)
        return channel

    def delete_channel(self, db: Session, channel_id: int) -> bool:
        """Delete a channel (soft delete)."""
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            return False

        channel.is_active = False
        channel.updated_at = datetime.utcnow()
        db.commit()
        return True

    def add_member(
        self, db: Session, channel_id: int, user_id: int, role: str = "member"
    ) -> bool:
        """Add a member to a channel."""
        return self._add_member_to_channel(db, channel_id, user_id, role)

    def _add_member_to_channel(self, db: Session, channel_id: int, user_id: int, role: str) -> bool:
        """Internal method to add member to channel."""
        # Check if already a member
        existing = db.execute(
            channel_members.select().where(
                and_(
                    channel_members.c.channel_id == channel_id,
                    channel_members.c.user_id == user_id
                )
            )
        ).first()
        
        if existing:
            return False
        
        # Add member
        db.execute(
            channel_members.insert().values(
                channel_id=channel_id,
                user_id=user_id,
                role=role,
                joined_at=datetime.utcnow()
            )
        )
        db.commit()
        return True

    def remove_member(self, db: Session, channel_id: int, user_id: int) -> bool:
        """Remove a member from a channel."""
        result = db.execute(
            channel_members.delete().where(
                and_(
                    channel_members.c.channel_id == channel_id,
                    channel_members.c.user_id == user_id,
                )
            )
        )
        db.commit()
        return result.rowcount > 0

    def get_channel_members(
        self, db: Session, channel_id: int
    ) -> List[channel_schemas.ChannelMember]:
        """Get all members of a channel."""
        members = db.execute(
            channel_members.select().where(channel_members.c.channel_id == channel_id)
        ).fetchall()

        return [
            channel_schemas.ChannelMember(
                user_id=member.user_id, role=member.role, joined_at=member.joined_at
            )
            for member in members
        ]

    def update_member_role(
        self, db: Session, channel_id: int, user_id: int, new_role: str
    ) -> bool:
        """Update a member's role in a channel."""
        result = db.execute(
            channel_members.update()
            .where(
                and_(
                    channel_members.c.channel_id == channel_id,
                    channel_members.c.user_id == user_id,
                )
            )
            .values(role=new_role)
        )
        db.commit()
        return result.rowcount > 0

    def get_channel_messages(
        self, db: Session, channel_id: int, skip: int = 0, limit: int = 50, days_back: int = 2
    ) -> List[channel_schemas.ChannelMessage]:
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
            .order_by(ChannelMessage.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [
            channel_schemas.ChannelMessage(
                id=msg.id,
                channel_id=msg.channel_id,
                user_id=msg.user_id,
                message=msg.message,
                response=msg.response,
                provider=msg.provider,
                message_type=msg.message_type,
                created_at=msg.created_at
            )
            for msg in messages
        ]

    def get_all_channel_messages(
        self, db: Session, channel_id: int, skip: int = 0, limit: int = 50
    ) -> List[channel_schemas.ChannelMessage]:
        """Get all messages from a specific channel (including archived)."""
        messages = (
            db.query(ChannelMessage)
            .filter(ChannelMessage.channel_id == channel_id)
            .order_by(ChannelMessage.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return [
            channel_schemas.ChannelMessage(
                id=msg.id,
                channel_id=msg.channel_id,
                user_id=msg.user_id,
                message=msg.message,
                response=msg.response,
                provider=msg.provider,
                message_type=msg.message_type,
                created_at=msg.created_at
            )
            for msg in messages
        ]

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

    def get_channel_stats(self, db: Session) -> channel_schemas.ChannelStats:
        """Get channel statistics for a tenant."""
        total_channels = db.query(Channel).count()
        active_channels = db.query(Channel).filter(Channel.is_active == True).count()
        private_channels = db.query(Channel).filter(Channel.is_private == True).count()

        total_messages = db.query(ChannelMessage).count()

        # Channels by creator
        creators = (
            db.query(Channel.created_by, func.count(Channel.id).label("count"))
            .group_by(Channel.created_by)
            .all()
        )

        channels_by_creator = {
            str(creator.created_by): creator.count for creator in creators
        }

        return channel_schemas.ChannelStats(
            total_channels=total_channels,
            active_channels=active_channels,
            private_channels=private_channels,
            total_messages=total_messages,
            channels_by_creator=channels_by_creator,
        )


# Global channel service instance
channel_service = ChannelService()
