"""
Memory model - User memory/preference entity
"""
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base
import uuid


class Memory(Base):
    """
    Memory model representing stored user information.
    
    Attributes:
        id: Unique identifier
        companion_id: Reference to the companion
        category: Memory category ('preference', 'fact', 'event')
        content: Memory content
        importance: Importance score (0-1)
        created_at: Creation timestamp
        last_accessed_at: Last access timestamp
    """
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    companion_id = Column(String(36), ForeignKey("companions.id"), nullable=False)
    category = Column(String(50), nullable=False)  # 'preference', 'fact', 'event'
    content = Column(Text, nullable=False)
    importance = Column(Float, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "companion_id": self.companion_id,
            "category": self.category,
            "content": self.content,
            "importance": self.importance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }
