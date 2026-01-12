"""
Books API Router - Book and reading position operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.book import Book, ReadingPosition
from services.book_service import book_service

router = APIRouter()


class BookCreate(BaseModel):
    """Schema for creating a book"""
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    content: str
    companion_id: Optional[str] = None


class ReadingPositionUpdate(BaseModel):
    """Schema for updating reading position"""
    chapter_index: int
    scroll_position: float = 0.0
    companion_id: Optional[str] = None


@router.post("/")
async def create_book(data: BookCreate, db: Session = Depends(get_db)):
    """Create a new book"""
    book = book_service.create_book(
        db,
        title=data.title,
        content=data.content,
        author=data.author,
        companion_id=data.companion_id,
        cover_url=data.cover_url
    )
    return book.to_dict()


@router.get("/")
async def list_books(
    companion_id: Optional[str] = Query(None, description="Filter by companion"),
    db: Session = Depends(get_db)
):
    """List all books"""
    books = book_service.list_books(db, companion_id)
    return [b.to_dict() for b in books]


@router.get("/{book_id}")
async def get_book(book_id: str, db: Session = Depends(get_db)):
    """Get a specific book by ID"""
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book.to_dict()


@router.delete("/{book_id}")
async def delete_book(book_id: str, db: Session = Depends(get_db)):
    """Delete a book"""
    success = book_service.delete_book(db, book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}


@router.get("/{book_id}/chapters")
async def get_chapters(book_id: str, db: Session = Depends(get_db)):
    """Get list of chapters for a book"""
    book = book_service.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    chapters = book_service.get_chapters_list(db, book_id)
    return chapters


@router.get("/{book_id}/chapters/{chapter_index}")
async def get_chapter(
    book_id: str,
    chapter_index: int,
    db: Session = Depends(get_db)
):
    """Get a specific chapter"""
    chapter = book_service.get_chapter(db, book_id, chapter_index)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.get("/{book_id}/position")
async def get_reading_position(
    book_id: str,
    companion_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get reading position for a book"""
    position = book_service.get_reading_position(db, book_id, companion_id)
    if not position:
        # Return default position if none exists
        return {
            "book_id": book_id,
            "companion_id": companion_id,
            "chapter_index": 0,
            "scroll_position": 0.0,
            "progress_percent": 0.0
        }
    return position.to_dict()


@router.put("/{book_id}/position")
async def update_reading_position(
    book_id: str, 
    data: ReadingPositionUpdate, 
    db: Session = Depends(get_db)
):
    """Update reading position for a book"""
    try:
        position = book_service.update_reading_position(
            db,
            book_id=book_id,
            chapter_index=data.chapter_index,
            scroll_position=data.scroll_position,
            companion_id=data.companion_id
        )
        return position.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
