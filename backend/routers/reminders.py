"""
Reminders API Router - Reminder management operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models.reminder import Reminder
from models.companion import Companion
from services.reminder_service import reminder_service

router = APIRouter()


class ReminderCreate(BaseModel):
    """Schema for creating a reminder"""
    companion_id: str
    type: str  # 'scheduled', 'greeting', 'checkin'
    message: str
    scheduled_time: Optional[datetime] = None
    repeat_pattern: Optional[str] = None
    enabled: Optional[bool] = True


class ReminderUpdate(BaseModel):
    """Schema for updating a reminder"""
    type: Optional[str] = None
    message: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    repeat_pattern: Optional[str] = None
    enabled: Optional[bool] = None


@router.post("/")
async def create_reminder(data: ReminderCreate, db: Session = Depends(get_db)):
    """Create a new reminder"""
    reminder = Reminder(
        companion_id=data.companion_id,
        type=data.type,
        message=data.message,
        scheduled_time=data.scheduled_time,
        repeat_pattern=data.repeat_pattern,
        enabled=data.enabled
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder.to_dict()


@router.get("/")
async def list_reminders(
    companion_id: str = Query(..., description="Companion ID to filter reminders"),
    db: Session = Depends(get_db)
):
    """List reminders for a companion"""
    reminders = (
        db.query(Reminder)
        .filter(Reminder.companion_id == companion_id)
        .all()
    )
    return [r.to_dict() for r in reminders]


# Static routes MUST come before dynamic routes like /{reminder_id}
@router.get("/pending")
async def get_pending_reminders(
    companion_id: str = Query(..., description="Companion ID"),
    db: Session = Depends(get_db)
):
    """Get pending reminders that should be triggered"""
    reminders = reminder_service.get_pending_reminders(db, companion_id)
    return [r.to_dict() for r in reminders]


@router.get("/active")
async def get_active_reminders(
    companion_id: str = Query(..., description="Companion ID"),
    db: Session = Depends(get_db)
):
    """Get all active (enabled) reminders"""
    reminders = reminder_service.get_active_reminders(db, companion_id)
    return [r.to_dict() for r in reminders]


@router.get("/inactivity")
async def check_inactivity(
    companion_id: str = Query(..., description="Companion ID"),
    threshold_hours: int = Query(24, description="Inactivity threshold in hours"),
    db: Session = Depends(get_db)
):
    """Check user inactivity status"""
    return reminder_service.check_user_inactivity(db, companion_id, threshold_hours)


@router.post("/greeting")
async def create_greeting(
    companion_id: str = Query(..., description="Companion ID"),
    greeting_type: str = Query(..., description="Greeting type: morning or evening"),
    db: Session = Depends(get_db)
):
    """Create a greeting reminder"""
    companion = db.query(Companion).filter(Companion.id == companion_id).first()
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    
    if greeting_type not in ["morning", "evening"]:
        raise HTTPException(status_code=400, detail="Invalid greeting type")
    
    reminder = reminder_service.create_greeting_reminder(
        db, companion_id, greeting_type, companion.name
    )
    return reminder.to_dict()


@router.post("/checkin")
async def create_checkin(
    companion_id: str = Query(..., description="Companion ID"),
    db: Session = Depends(get_db)
):
    """Create a check-in reminder for inactive user"""
    companion = db.query(Companion).filter(Companion.id == companion_id).first()
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    
    reminder = reminder_service.create_checkin_reminder(db, companion_id, companion.name)
    return reminder.to_dict()


# Dynamic routes with path parameters MUST come after static routes
@router.get("/{reminder_id}")
async def get_reminder(reminder_id: str, db: Session = Depends(get_db)):
    """Get a specific reminder by ID"""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder.to_dict()


@router.put("/{reminder_id}")
async def update_reminder(
    reminder_id: str, 
    data: ReminderUpdate, 
    db: Session = Depends(get_db)
):
    """Update a reminder"""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reminder, key, value)
    
    db.commit()
    db.refresh(reminder)
    return reminder.to_dict()


@router.put("/{reminder_id}/toggle")
async def toggle_reminder(
    reminder_id: str,
    db: Session = Depends(get_db)
):
    """Toggle reminder enabled status"""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    reminder.enabled = not reminder.enabled
    db.commit()
    db.refresh(reminder)
    return reminder.to_dict()


@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: str, db: Session = Depends(get_db)):
    """Delete a reminder"""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    db.delete(reminder)
    db.commit()
    return {"message": "Reminder deleted successfully"}
