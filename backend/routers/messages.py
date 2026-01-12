"""
Messages API Router - Chat message operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from models.message import Message
from models.companion import Companion
from services.chat_service import ChatService

router = APIRouter()


class MessageCreate(BaseModel):
    """Schema for creating a message"""
    companion_id: str
    role: str  # 'user' or 'companion'
    content: str
    audio_url: Optional[str] = None


class ChatRequest(BaseModel):
    """Schema for chat request"""
    companion_id: str
    content: str


@router.post("/")
async def create_message(data: MessageCreate, db: Session = Depends(get_db)):
    """Create a new message"""
    message = Message(
        companion_id=data.companion_id,
        role=data.role,
        content=data.content,
        audio_url=data.audio_url
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message.to_dict()


@router.post("/chat")
async def chat(
    data: ChatRequest, 
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    x_group_id: Optional[str] = Header(None, alias="X-Group-Id")
):
    """Send a message and get AI response"""
    # Get companion
    companion = db.query(Companion).filter(Companion.id == data.companion_id).first()
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    
    # Get conversation history
    history = (
        db.query(Message)
        .filter(Message.companion_id == data.companion_id)
        .order_by(Message.timestamp.desc())
        .limit(20)
        .all()
    )
    history_list = [{"role": m.role, "content": m.content} for m in reversed(history)] if history else []
    
    # Save user message
    user_message = Message(
        companion_id=data.companion_id,
        role="user",
        content=data.content
    )
    db.add(user_message)
    db.commit()
    
    # Create chat service with API key from header or env
    # Ensure empty strings are treated as None
    api_key = x_api_key if x_api_key else None
    group_id = x_group_id if x_group_id else None
    chat_service = ChatService(api_key=api_key, group_id=group_id)
    
    # Get AI response
    response_text = await chat_service.send_message(
        user_message=data.content,
        companion_name=companion.name or "AI助手",
        personality=companion.personality or "友好、温暖、善解人意",
        history=history_list
    )
    
    # Save AI response
    ai_message = Message(
        companion_id=data.companion_id,
        role="companion",
        content=response_text
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    return ai_message.to_dict()


@router.get("/")
async def list_messages(
    companion_id: str = Query(..., description="Companion ID to filter messages"),
    limit: int = Query(50, description="Maximum number of messages to return"),
    db: Session = Depends(get_db)
):
    """List messages for a companion"""
    messages = (
        db.query(Message)
        .filter(Message.companion_id == companion_id)
        .order_by(Message.timestamp.asc())
        .limit(limit)
        .all()
    )
    return [m.to_dict() for m in messages]


@router.get("/{message_id}")
async def get_message(message_id: str, db: Session = Depends(get_db)):
    """Get a specific message by ID"""
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message.to_dict()


@router.delete("/companion/{companion_id}")
async def clear_history(companion_id: str, db: Session = Depends(get_db)):
    """Clear all messages for a companion"""
    db.query(Message).filter(Message.companion_id == companion_id).delete()
    db.commit()
    return {"message": "Chat history cleared"}
