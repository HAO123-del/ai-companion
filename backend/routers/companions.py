"""
Companions API Router - CRUD operations for AI companions
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models.companion import Companion

router = APIRouter()


class CompanionCreate(BaseModel):
    """Schema for creating a companion"""
    name: str
    personality: str
    avatar_url: Optional[str] = None
    avatar_primary_color: Optional[str] = "#8B5CF6"
    avatar_secondary_color: Optional[str] = "#6366F1"
    avatar_style: Optional[str] = "gradient"
    voice_id: Optional[str] = None
    voice_type: Optional[str] = "preset"


class CompanionUpdate(BaseModel):
    """Schema for updating a companion"""
    name: Optional[str] = None
    personality: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_primary_color: Optional[str] = None
    avatar_secondary_color: Optional[str] = None
    avatar_style: Optional[str] = None
    voice_id: Optional[str] = None
    voice_type: Optional[str] = None


@router.post("/")
async def create_companion(data: CompanionCreate, db: Session = Depends(get_db)):
    """Create a new companion"""
    companion = Companion(
        name=data.name,
        personality=data.personality,
        avatar_url=data.avatar_url,
        avatar_primary_color=data.avatar_primary_color,
        avatar_secondary_color=data.avatar_secondary_color,
        avatar_style=data.avatar_style,
        voice_id=data.voice_id,
        voice_type=data.voice_type
    )
    db.add(companion)
    db.commit()
    db.refresh(companion)
    return companion.to_dict()


@router.get("/")
async def list_companions(db: Session = Depends(get_db)):
    """List all companions"""
    companions = db.query(Companion).all()
    return [c.to_dict() for c in companions]


@router.get("/{companion_id}")
async def get_companion(companion_id: str, db: Session = Depends(get_db)):
    """Get a specific companion by ID"""
    companion = db.query(Companion).filter(Companion.id == companion_id).first()
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    return companion.to_dict()


@router.put("/{companion_id}")
async def update_companion(
    companion_id: str, 
    data: CompanionUpdate, 
    db: Session = Depends(get_db)
):
    """Update a companion"""
    companion = db.query(Companion).filter(Companion.id == companion_id).first()
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(companion, key, value)
    
    companion.last_active_at = datetime.utcnow()
    db.commit()
    db.refresh(companion)
    return companion.to_dict()


@router.delete("/{companion_id}")
async def delete_companion(companion_id: str, db: Session = Depends(get_db)):
    """Delete a companion"""
    companion = db.query(Companion).filter(Companion.id == companion_id).first()
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    
    db.delete(companion)
    db.commit()
    return {"message": "Companion deleted successfully"}
