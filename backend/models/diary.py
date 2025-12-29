"""
DiaryEntry model - Diary and mood tracking entity
"""
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.sql import func
from database import Base
import uuid


class DiaryEntry(Base):
    """
    DiaryEntry model representing a diary entry with mood.
    
    Attributes:
        id: Unique identifier
        content: Diary entry content
        mood: Mood category ('happy', 'neutral', 'sad', 'anxious', 'excited')
        mood_score: Numeric mood score (1-5)
        tags: Comma-separated tags
        created_at: Entry timestamp
    """
    __tablename__ = "diary_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    mood = Column(String(20), nullable=False)  # 'happy', 'neutral', 'sad', 'anxious', 'excited'
    mood_score = Column(Integer, nullable=True)  # 1-5
    tags = Column(Text, nullable=True)  # Comma-separated
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "mood": self.mood,
            "mood_score": self.mood_score,
            "tags": self.tags.split(",") if self.tags else [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
