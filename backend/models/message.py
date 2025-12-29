"""
Message model - Chat message entity
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base
import uuid


class Message(Base):
    """
    Message model representing a chat message.
    
    Attributes:
        id: Unique identifier
        companion_id: Reference to the companion
        role: Message sender role ('user' or 'companion')
        content: Message text content
        audio_url: Optional URL to audio file
        timestamp: Message timestamp
    """
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    companion_id = Column(String(36), ForeignKey("companions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'companion'
    content = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "companion_id": self.companion_id,
            "role": self.role,
            "content": self.content,
            "audio_url": self.audio_url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
