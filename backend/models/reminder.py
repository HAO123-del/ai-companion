"""
Reminder model - Scheduled reminder entity
"""
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from database import Base
import uuid


class Reminder(Base):
    """
    Reminder model representing a scheduled reminder.
    
    Attributes:
        id: Unique identifier
        companion_id: Reference to the companion
        type: Reminder type ('scheduled', 'greeting', 'checkin')
        message: Reminder message content
        scheduled_time: When the reminder should trigger
        repeat_pattern: Cron expression for recurring reminders
        enabled: Whether the reminder is active
    """
    __tablename__ = "reminders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    companion_id = Column(String(36), ForeignKey("companions.id"), nullable=False)
    type = Column(String(20), nullable=False)  # 'scheduled', 'greeting', 'checkin'
    message = Column(Text, nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    repeat_pattern = Column(String(100), nullable=True)
    enabled = Column(Boolean, default=True)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "companion_id": self.companion_id,
            "type": self.type,
            "message": self.message,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "repeat_pattern": self.repeat_pattern,
            "enabled": self.enabled
        }
