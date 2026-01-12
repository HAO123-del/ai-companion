"""
Reminder Service - Scheduling and notification management
Handles reminder scheduling, greeting logic, and inactivity detection
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from models.reminder import Reminder
from models.companion import Companion
from models.message import Message


class ReminderService:
    """
    Service for managing reminders and scheduled notifications.
    Provides greeting logic, inactivity detection, and reminder scheduling.
    """
    
    def __init__(self):
        # Default greeting times (24-hour format)
        self.morning_greeting_hour = 8
        self.evening_greeting_hour = 21
        # Inactivity threshold in hours
        self.inactivity_threshold_hours = 24
    
    def get_pending_reminders(
        self,
        db: Session,
        companion_id: str,
        current_time: Optional[datetime] = None
    ) -> List[Reminder]:
        """
        Get reminders that should be triggered at or before the current time.
        
        Args:
            db: Database session
            companion_id: ID of the companion
            current_time: Current time (defaults to now)
            
        Returns:
            List of pending Reminder objects
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        reminders = (
            db.query(Reminder)
            .filter(
                Reminder.companion_id == companion_id,
                Reminder.enabled == True,
                Reminder.scheduled_time <= current_time
            )
            .all()
        )
        
        return reminders
    
    def get_active_reminders(
        self,
        db: Session,
        companion_id: str
    ) -> List[Reminder]:
        """
        Get all active (enabled) reminders for a companion.
        
        Args:
            db: Database session
            companion_id: ID of the companion
            
        Returns:
            List of active Reminder objects
        """
        reminders = (
            db.query(Reminder)
            .filter(
                Reminder.companion_id == companion_id,
                Reminder.enabled == True
            )
            .all()
        )
        
        return reminders
    
    def should_send_morning_greeting(
        self,
        db: Session,
        companion_id: str,
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if a morning greeting should be sent.
        
        Args:
            db: Database session
            companion_id: ID of the companion
            current_time: Current time (defaults to now)
            
        Returns:
            True if morning greeting should be sent
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Check if it's morning greeting time
        if current_time.hour != self.morning_greeting_hour:
            return False
        
        # Check if greeting was already sent today
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        existing_greeting = (
            db.query(Reminder)
            .filter(
                Reminder.companion_id == companion_id,
                Reminder.type == "greeting",
                Reminder.scheduled_time >= today_start,
                Reminder.message.like("%早安%")
            )
            .first()
        )
        
        return existing_greeting is None
    
    def should_send_evening_greeting(
        self,
        db: Session,
        companion_id: str,
        current_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if an evening greeting should be sent.
        
        Args:
            db: Database session
            companion_id: ID of the companion
            current_time: Current time (defaults to now)
            
        Returns:
            True if evening greeting should be sent
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Check if it's evening greeting time
        if current_time.hour != self.evening_greeting_hour:
            return False
        
        # Check if greeting was already sent today
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        existing_greeting = (
            db.query(Reminder)
            .filter(
                Reminder.companion_id == companion_id,
                Reminder.type == "greeting",
                Reminder.scheduled_time >= today_start,
                Reminder.message.like("%晚安%")
            )
            .first()
        )
        
        return existing_greeting is None
    
    def check_user_inactivity(
        self,
        db: Session,
        companion_id: str,
        threshold_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if the user has been inactive for too long.
        
        Args:
            db: Database session
            companion_id: ID of the companion
            threshold_hours: Inactivity threshold in hours
            
        Returns:
            Dictionary with inactivity status and details
        """
        if threshold_hours is None:
            threshold_hours = self.inactivity_threshold_hours
        
        # Get the last user message
        last_message = (
            db.query(Message)
            .filter(
                Message.companion_id == companion_id,
                Message.role == "user"
            )
            .order_by(Message.timestamp.desc())
            .first()
        )
        
        if last_message is None:
            return {
                "is_inactive": False,
                "last_activity": None,
                "hours_inactive": None,
                "should_checkin": False
            }
        
        current_time = datetime.utcnow()
        time_since_last = current_time - last_message.timestamp
        hours_inactive = time_since_last.total_seconds() / 3600
        
        is_inactive = hours_inactive >= threshold_hours
        
        return {
            "is_inactive": is_inactive,
            "last_activity": last_message.timestamp.isoformat(),
            "hours_inactive": round(hours_inactive, 1),
            "should_checkin": is_inactive
        }
    
    def create_greeting_reminder(
        self,
        db: Session,
        companion_id: str,
        greeting_type: str,
        companion_name: str
    ) -> Reminder:
        """
        Create a greeting reminder.
        
        Args:
            db: Database session
            companion_id: ID of the companion
            greeting_type: 'morning' or 'evening'
            companion_name: Name of the companion
            
        Returns:
            Created Reminder object
        """
        if greeting_type == "morning":
            message = f"早安！{companion_name}来陪你开始新的一天啦~"
        else:
            message = f"晚安！{companion_name}祝你有个好梦~"
        
        reminder = Reminder(
            companion_id=companion_id,
            type="greeting",
            message=message,
            scheduled_time=datetime.utcnow(),
            enabled=True
        )
        
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        
        return reminder
    
    def create_checkin_reminder(
        self,
        db: Session,
        companion_id: str,
        companion_name: str
    ) -> Reminder:
        """
        Create a check-in reminder for inactive user.
        
        Args:
            db: Database session
            companion_id: ID of the companion
            companion_name: Name of the companion
            
        Returns:
            Created Reminder object
        """
        message = f"好久不见！{companion_name}想你了，最近怎么样？ 💭"
        
        reminder = Reminder(
            companion_id=companion_id,
            type="checkin",
            message=message,
            scheduled_time=datetime.utcnow(),
            enabled=True
        )
        
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        
        return reminder
    
    def get_due_reminders_by_type(
        self,
        db: Session,
        companion_id: str,
        reminder_type: str
    ) -> List[Reminder]:
        """
        Get due reminders of a specific type.
        
        Args:
            db: Database session
            companion_id: ID of the companion
            reminder_type: Type of reminder to filter
            
        Returns:
            List of due Reminder objects
        """
        current_time = datetime.utcnow()
        
        reminders = (
            db.query(Reminder)
            .filter(
                Reminder.companion_id == companion_id,
                Reminder.type == reminder_type,
                Reminder.enabled == True,
                Reminder.scheduled_time <= current_time
            )
            .all()
        )
        
        return reminders


# Global instance
reminder_service = ReminderService()
