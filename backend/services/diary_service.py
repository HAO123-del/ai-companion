"""
Diary Service - Business logic for diary and mood tracking
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.diary import DiaryEntry


class DiaryService:
    """
    Service for managing diary entries and mood tracking.
    
    Provides CRUD operations, mood statistics, and trend analysis.
    """
    
    VALID_MOODS = ['happy', 'neutral', 'sad', 'anxious', 'excited']
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_entry(
        self,
        content: str,
        mood: str,
        mood_score: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> DiaryEntry:
        """
        Create a new diary entry.
        
        Args:
            content: Diary entry content
            mood: Mood category
            mood_score: Numeric mood score (1-5)
            tags: List of tags
            
        Returns:
            Created DiaryEntry
            
        Raises:
            ValueError: If mood is invalid or mood_score out of range
        """
        if mood not in self.VALID_MOODS:
            raise ValueError(f"Invalid mood. Must be one of: {self.VALID_MOODS}")
        
        if mood_score is not None and (mood_score < 1 or mood_score > 5):
            raise ValueError("mood_score must be between 1 and 5")
        
        entry = DiaryEntry(
            content=content,
            mood=mood,
            mood_score=mood_score,
            tags=",".join(tags) if tags else None
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def get_entry(self, entry_id: str) -> Optional[DiaryEntry]:
        """Get a diary entry by ID"""
        return self.db.query(DiaryEntry).filter(DiaryEntry.id == entry_id).first()
    
    def update_entry(
        self,
        entry_id: str,
        content: Optional[str] = None,
        mood: Optional[str] = None,
        mood_score: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[DiaryEntry]:
        """
        Update a diary entry.
        
        Args:
            entry_id: Entry ID to update
            content: New content (optional)
            mood: New mood (optional)
            mood_score: New mood score (optional)
            tags: New tags (optional)
            
        Returns:
            Updated DiaryEntry or None if not found
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return None
        
        if content is not None:
            entry.content = content
        if mood is not None:
            if mood not in self.VALID_MOODS:
                raise ValueError(f"Invalid mood. Must be one of: {self.VALID_MOODS}")
            entry.mood = mood
        if mood_score is not None:
            if mood_score < 1 or mood_score > 5:
                raise ValueError("mood_score must be between 1 and 5")
            entry.mood_score = mood_score
        if tags is not None:
            entry.tags = ",".join(tags) if tags else None
        
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        Delete a diary entry.
        
        Returns:
            True if deleted, False if not found
        """
        entry = self.get_entry(entry_id)
        if not entry:
            return False
        
        self.db.delete(entry)
        self.db.commit()
        return True
    
    def list_entries(
        self,
        limit: int = 50,
        offset: int = 0,
        mood_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        order_desc: bool = True
    ) -> List[DiaryEntry]:
        """
        List diary entries with optional filtering.
        
        Args:
            limit: Maximum entries to return
            offset: Number of entries to skip
            mood_filter: Filter by mood
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            order_desc: True for newest first, False for oldest first
            
        Returns:
            List of DiaryEntry objects
        """
        query = self.db.query(DiaryEntry)
        
        if mood_filter:
            query = query.filter(DiaryEntry.mood == mood_filter)
        if start_date:
            query = query.filter(DiaryEntry.created_at >= start_date)
        if end_date:
            query = query.filter(DiaryEntry.created_at <= end_date)
        
        if order_desc:
            query = query.order_by(DiaryEntry.created_at.desc())
        else:
            query = query.order_by(DiaryEntry.created_at.asc())
        
        return query.offset(offset).limit(limit).all()
    
    def get_mood_stats(self, period: str = "week") -> Dict[str, Any]:
        """
        Calculate mood statistics for a time period.
        
        Args:
            period: 'week' or 'month'
            
        Returns:
            Dictionary with statistics including:
            - period: The time period
            - average_score: Average mood score
            - mood_distribution: Count of each mood
            - trend: 'improving', 'stable', or 'declining'
            - total_entries: Number of entries in period
        """
        now = datetime.utcnow()
        if period == "week":
            start_date = now - timedelta(days=7)
            half_period = timedelta(days=3)
        else:
            start_date = now - timedelta(days=30)
            half_period = timedelta(days=15)
        
        entries = self.list_entries(
            limit=1000,
            start_date=start_date,
            order_desc=False
        )
        
        if not entries:
            return {
                "period": period,
                "average_score": 0,
                "mood_distribution": {},
                "trend": "stable",
                "total_entries": 0
            }
        
        # Calculate average score
        scores = [e.mood_score for e in entries if e.mood_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Calculate mood distribution
        mood_distribution = {}
        for e in entries:
            mood_distribution[e.mood] = mood_distribution.get(e.mood, 0) + 1
        
        # Calculate trend by comparing first half vs second half
        mid_date = start_date + half_period
        first_half_scores = [
            e.mood_score for e in entries 
            if e.mood_score and e.created_at < mid_date
        ]
        second_half_scores = [
            e.mood_score for e in entries 
            if e.mood_score and e.created_at >= mid_date
        ]
        
        trend = "stable"
        if first_half_scores and second_half_scores:
            first_avg = sum(first_half_scores) / len(first_half_scores)
            second_avg = sum(second_half_scores) / len(second_half_scores)
            diff = second_avg - first_avg
            if diff > 0.5:
                trend = "improving"
            elif diff < -0.5:
                trend = "declining"
        
        return {
            "period": period,
            "average_score": round(avg_score, 2),
            "mood_distribution": mood_distribution,
            "trend": trend,
            "total_entries": len(entries)
        }
    
    def log_mood(self, mood: str, note: Optional[str] = None) -> DiaryEntry:
        """
        Quick mood log without full diary entry.
        
        Args:
            mood: Mood category
            note: Optional short note
            
        Returns:
            Created DiaryEntry
        """
        # Map mood to default score
        mood_scores = {
            'happy': 5,
            'excited': 4,
            'neutral': 3,
            'anxious': 2,
            'sad': 1
        }
        
        content = note or f"Mood logged: {mood}"
        mood_score = mood_scores.get(mood, 3)
        
        return self.create_entry(
            content=content,
            mood=mood,
            mood_score=mood_score,
            tags=["mood_log"]
        )
