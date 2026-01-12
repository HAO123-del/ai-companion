"""
Diary API Router - Diary entry and mood tracking operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from models.diary import DiaryEntry

router = APIRouter()


class DiaryEntryCreate(BaseModel):
    """Schema for creating a diary entry"""
    content: str
    mood: str  # 'happy', 'neutral', 'sad', 'anxious', 'excited'
    mood_score: Optional[int] = None  # 1-5
    tags: Optional[List[str]] = None


class DiaryEntryUpdate(BaseModel):
    """Schema for updating a diary entry"""
    content: Optional[str] = None
    mood: Optional[str] = None
    mood_score: Optional[int] = None
    tags: Optional[List[str]] = None


@router.post("/")
async def create_entry(data: DiaryEntryCreate, db: Session = Depends(get_db)):
    """Create a new diary entry"""
    entry = DiaryEntry(
        content=data.content,
        mood=data.mood,
        mood_score=data.mood_score,
        tags=",".join(data.tags) if data.tags else None
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry.to_dict()


@router.get("/")
async def list_entries(
    limit: int = Query(50, description="Maximum number of entries to return"),
    db: Session = Depends(get_db)
):
    """List diary entries in chronological order"""
    entries = (
        db.query(DiaryEntry)
        .order_by(DiaryEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    return [e.to_dict() for e in entries]


@router.get("/stats")
async def get_mood_stats(
    period: str = Query("week", description="Period for stats: 'week' or 'month'"),
    db: Session = Depends(get_db)
):
    """Get mood statistics for a period"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    else:
        start_date = now - timedelta(days=30)
    
    entries = (
        db.query(DiaryEntry)
        .filter(DiaryEntry.created_at >= start_date)
        .all()
    )
    
    if not entries:
        return {
            "period": period,
            "average_score": 0,
            "mood_distribution": {},
            "trend": "stable",
            "total_entries": 0
        }
    
    # Calculate statistics
    scores = [e.mood_score for e in entries if e.mood_score]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    mood_counts = {}
    for e in entries:
        mood_counts[e.mood] = mood_counts.get(e.mood, 0) + 1
    
    return {
        "period": period,
        "average_score": round(avg_score, 2),
        "mood_distribution": mood_counts,
        "trend": "stable",  # Simplified - could be enhanced
        "total_entries": len(entries)
    }


@router.get("/{entry_id}")
async def get_entry(entry_id: str, db: Session = Depends(get_db)):
    """Get a specific diary entry by ID"""
    entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    return entry.to_dict()


@router.put("/{entry_id}")
async def update_entry(
    entry_id: str, 
    data: DiaryEntryUpdate, 
    db: Session = Depends(get_db)
):
    """Update a diary entry"""
    entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    
    update_data = data.model_dump(exclude_unset=True)
    if "tags" in update_data and update_data["tags"] is not None:
        update_data["tags"] = ",".join(update_data["tags"])
    
    for key, value in update_data.items():
        setattr(entry, key, value)
    
    db.commit()
    db.refresh(entry)
    return entry.to_dict()


@router.delete("/{entry_id}")
async def delete_entry(entry_id: str, db: Session = Depends(get_db)):
    """Delete a diary entry"""
    entry = db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    
    db.delete(entry)
    db.commit()
    return {"message": "Diary entry deleted successfully"}
