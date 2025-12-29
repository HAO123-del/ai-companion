"""
Memories API Router - Memory management operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from models.memory import Memory

router = APIRouter()


class MemoryCreate(BaseModel):
    """Schema for creating a memory"""
    companion_id: str
    category: str  # 'preference', 'fact', 'event'
    content: str
    importance: Optional[float] = 0.5


class MemoryUpdate(BaseModel):
    """Schema for updating a memory"""
    category: Optional[str] = None
    content: Optional[str] = None
    importance: Optional[float] = None


@router.post("/")
async def create_memory(data: MemoryCreate, db: Session = Depends(get_db)):
    """Create a new memory"""
    memory = Memory(
        companion_id=data.companion_id,
        category=data.category,
        content=data.content,
        importance=data.importance
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return memory.to_dict()


@router.get("/")
async def list_memories(
    companion_id: str = Query(..., description="Companion ID to filter memories"),
    sort_by: str = Query("importance", description="Sort by: importance, access_time, created_at"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    List memories for a companion with sorting options.
    
    Sort options:
    - importance: Sort by importance score (desc) then created_at (desc)
    - access_time: Sort by last_accessed_at (desc) then importance (desc)
    - created_at: Sort by creation time (desc)
    """
    query = db.query(Memory).filter(Memory.companion_id == companion_id)
    
    # Apply category filter if provided
    if category:
        query = query.filter(Memory.category == category)
    
    # Apply sorting based on sort_by parameter
    if sort_by == "access_time":
        # Sort by last accessed time, with null values last
        query = query.order_by(
            Memory.last_accessed_at.desc().nullslast(),
            Memory.importance.desc()
        )
    elif sort_by == "created_at":
        query = query.order_by(Memory.created_at.desc())
    else:  # default: importance
        query = query.order_by(
            Memory.importance.desc(),
            Memory.created_at.desc()
        )
    
    # Apply limit if provided
    if limit:
        query = query.limit(limit)
    
    memories = query.all()
    return [m.to_dict() for m in memories]


@router.get("/relevant")
async def get_relevant_memories(
    companion_id: str = Query(..., description="Companion ID"),
    context: str = Query(..., description="Context to match against"),
    limit: int = Query(5, description="Maximum number of memories to return"),
    db: Session = Depends(get_db)
):
    """
    Get memories relevant to a given context.
    Uses simple keyword matching for relevance.
    """
    # Get all memories for the companion
    memories = (
        db.query(Memory)
        .filter(Memory.companion_id == companion_id)
        .all()
    )
    
    # Simple relevance scoring based on keyword matching
    context_words = set(context.lower().split())
    scored_memories = []
    
    for memory in memories:
        content_words = set(memory.content.lower().split())
        # Calculate overlap score
        overlap = len(context_words & content_words)
        if overlap > 0:
            # Combine keyword match with importance
            relevance_score = overlap * 0.5 + memory.importance * 0.5
            scored_memories.append((memory, relevance_score))
    
    # Sort by relevance score and take top N
    scored_memories.sort(key=lambda x: x[1], reverse=True)
    top_memories = scored_memories[:limit]
    
    # Update last_accessed_at for retrieved memories
    for memory, _ in top_memories:
        memory.last_accessed_at = datetime.utcnow()
    db.commit()
    
    return [m.to_dict() for m, _ in top_memories]


@router.get("/{memory_id}")
async def get_memory(memory_id: str, db: Session = Depends(get_db)):
    """Get a specific memory by ID"""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Update last accessed time
    memory.last_accessed_at = datetime.utcnow()
    db.commit()
    db.refresh(memory)
    return memory.to_dict()


@router.put("/{memory_id}")
async def update_memory(
    memory_id: str, 
    data: MemoryUpdate, 
    db: Session = Depends(get_db)
):
    """Update a memory"""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(memory, key, value)
    
    db.commit()
    db.refresh(memory)
    return memory.to_dict()


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    """Delete a memory"""
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    db.delete(memory)
    db.commit()
    return {"message": "Memory deleted successfully"}
