"""
Book and ReadingPosition models - Book reading entities
"""
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.sql import func
from database import Base
import uuid


class Book(Base):
    """
    Book model representing an uploaded book.
    
    Attributes:
        id: Unique identifier
        companion_id: Associated companion
        title: Book title
        author: Book author
        cover_url: URL or path to cover image
        content: Book content (text)
        total_chapters: Number of chapters
        created_at: Upload timestamp
    """
    __tablename__ = "books"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    companion_id = Column(String(36), ForeignKey("companions.id"), nullable=True)
    title = Column(String(200), nullable=False)
    author = Column(String(100), nullable=True)
    cover_url = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    total_chapters = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "companion_id": self.companion_id,
            "title": self.title,
            "author": self.author,
            "cover_url": self.cover_url,
            "content": self.content,
            "total_chapters": self.total_chapters,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ReadingPosition(Base):
    """
    ReadingPosition model representing reading progress.
    
    Attributes:
        id: Unique identifier
        book_id: Reference to the book
        companion_id: Associated companion
        chapter_index: Current chapter index
        scroll_position: Scroll position within chapter
        progress_percent: Overall reading progress (0-100)
        updated_at: Last update timestamp
    """
    __tablename__ = "reading_positions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String(36), ForeignKey("books.id"), nullable=False)
    companion_id = Column(String(36), ForeignKey("companions.id"), nullable=True)
    chapter_index = Column(Integer, default=0)
    scroll_position = Column(Float, default=0.0)
    progress_percent = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "book_id": self.book_id,
            "companion_id": self.companion_id,
            "chapter_index": self.chapter_index,
            "scroll_position": self.scroll_position,
            "progress_percent": self.progress_percent,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
