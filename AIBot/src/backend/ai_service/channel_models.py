# Import models from the main channels module to avoid duplication
from src.backend.channels.models import Channel, ChannelMessage, channel_members

# Re-export for backward compatibility
__all__ = ['Channel', 'ChannelMessage', 'channel_members']
