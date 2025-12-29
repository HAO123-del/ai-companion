"""
Companion model - AI companion entity
"""
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.sql import func
from database import Base
import uuid


class Companion(Base):
    """
    Companion model representing an AI companion entity.
    
    Attributes:
        id: Unique identifier
        name: Display name of the companion
        personality: Personality description used for prompts
        avatar_url: URL or path to avatar image
        avatar_primary_color: Primary color for avatar (hex)
        avatar_secondary_color: Secondary color for avatar (hex)
        avatar_style: Avatar style ('gradient', 'solid', 'outline')
        voice_id: MiniMax voice ID for TTS
        voice_type: Type of voice ('cloned' or 'preset')
        created_at: Creation timestamp
        last_active_at: Last activity timestamp
    """
    __tablename__ = "companions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    personality = Column(Text, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    avatar_primary_color = Column(String(20), default="#8B5CF6")
    avatar_secondary_color = Column(String(20), default="#6366F1")
    avatar_style = Column(String(20), default="gradient")
    voice_id = Column(String(100), nullable=True)
    voice_type = Column(String(20), default="preset")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "personality": self.personality,
            "avatar_url": self.avatar_url,
            "avatar_primary_color": self.avatar_primary_color,
            "avatar_secondary_color": self.avatar_secondary_color,
            "avatar_style": self.avatar_style,
            "voice_id": self.voice_id,
            "voice_type": self.voice_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None
        }
