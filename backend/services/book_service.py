"""
Book Service - Book management and reading progress
Handles book upload, parsing, and reading position tracking
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import re

from models.book import Book, ReadingPosition


class BookService:
    """
    Service for managing books and reading progress.
    Provides book parsing, chapter extraction, and position tracking.
    """
    
    def parse_chapters(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse book content into chapters.
        
        Looks for chapter markers like:
        - 第X章
        - Chapter X
        - CHAPTER X
        - 第X节
        
        Args:
            content: Raw book content
            
        Returns:
            List of chapter dictionaries with title and content
        """
        # Common chapter patterns
        patterns = [
            r'(第[一二三四五六七八九十百千\d]+章[^\n]*)',
            r'(Chapter\s+\d+[^\n]*)',
            r'(CHAPTER\s+\d+[^\n]*)',
            r'(第[一二三四五六七八九十百千\d]+节[^\n]*)',
        ]
        
        combined_pattern = '|'.join(patterns)
        
        # Find all chapter markers
        matches = list(re.finditer(combined_pattern, content, re.IGNORECASE))
        
        if not matches:
            # No chapters found, treat entire content as one chapter
            return [{
                "index": 0,
                "title": "全文",
                "content": content.strip()
            }]
        
        chapters = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            
            chapter_content = content[start:end].strip()
            chapter_title = match.group(0).strip()
            
            chapters.append({
                "index": i,
                "title": chapter_title,
                "content": chapter_content
            })
        
        return chapters
    
    def create_book(
        self,
        db: Session,
        title: str,
        content: str,
        author: Optional[str] = None,
        companion_id: Optional[str] = None,
        cover_url: Optional[str] = None
    ) -> Book:
        """
        Create a new book with parsed chapters.
        
        Args:
            db: Database session
            title: Book title
            content: Book content
            author: Book author
            companion_id: Associated companion ID
            cover_url: Cover image URL
            
        Returns:
            Created Book object
        """
        chapters = self.parse_chapters(content)
        
        book = Book(
            title=title,
            author=author,
            content=content,
            companion_id=companion_id,
            cover_url=cover_url,
            total_chapters=len(chapters)
        )
        
        db.add(book)
        db.commit()
        db.refresh(book)
        
        return book
    
    def get_book(self, db: Session, book_id: str) -> Optional[Book]:
        """Get a book by ID"""
        return db.query(Book).filter(Book.id == book_id).first()
    
    def list_books(
        self,
        db: Session,
        companion_id: Optional[str] = None
    ) -> List[Book]:
        """List books, optionally filtered by companion"""
        query = db.query(Book)
        if companion_id:
            query = query.filter(Book.companion_id == companion_id)
        return query.all()
    
    def delete_book(self, db: Session, book_id: str) -> bool:
        """Delete a book and its reading positions"""
        book = self.get_book(db, book_id)
        if not book:
            return False
        
        # Delete reading positions
        db.query(ReadingPosition).filter(
            ReadingPosition.book_id == book_id
        ).delete()
        
        db.delete(book)
        db.commit()
        return True
    
    def get_chapter(
        self,
        db: Session,
        book_id: str,
        chapter_index: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific chapter from a book.
        
        Args:
            db: Database session
            book_id: Book ID
            chapter_index: Chapter index (0-based)
            
        Returns:
            Chapter dictionary or None
        """
        book = self.get_book(db, book_id)
        if not book:
            return None
        
        chapters = self.parse_chapters(book.content)
        
        if chapter_index < 0 or chapter_index >= len(chapters):
            return None
        
        return chapters[chapter_index]
    
    def get_chapters_list(
        self,
        db: Session,
        book_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get list of chapters (titles only) for a book.
        
        Args:
            db: Database session
            book_id: Book ID
            
        Returns:
            List of chapter info (index and title)
        """
        book = self.get_book(db, book_id)
        if not book:
            return []
        
        chapters = self.parse_chapters(book.content)
        
        return [
            {"index": c["index"], "title": c["title"]}
            for c in chapters
        ]
    
    def get_reading_position(
        self,
        db: Session,
        book_id: str,
        companion_id: Optional[str] = None
    ) -> Optional[ReadingPosition]:
        """Get reading position for a book"""
        query = db.query(ReadingPosition).filter(
            ReadingPosition.book_id == book_id
        )
        if companion_id:
            query = query.filter(ReadingPosition.companion_id == companion_id)
        return query.first()
    
    def update_reading_position(
        self,
        db: Session,
        book_id: str,
        chapter_index: int,
        scroll_position: float = 0.0,
        companion_id: Optional[str] = None
    ) -> ReadingPosition:
        """
        Update reading position for a book.
        
        Args:
            db: Database session
            book_id: Book ID
            chapter_index: Current chapter index
            scroll_position: Scroll position within chapter
            companion_id: Associated companion ID
            
        Returns:
            Updated ReadingPosition object
        """
        book = self.get_book(db, book_id)
        if not book:
            raise ValueError("Book not found")
        
        # Calculate progress percentage
        progress_percent = 0.0
        if book.total_chapters > 0:
            progress_percent = ((chapter_index + 1) / book.total_chapters) * 100
        
        # Get or create position
        position = self.get_reading_position(db, book_id, companion_id)
        
        if not position:
            position = ReadingPosition(
                book_id=book_id,
                companion_id=companion_id
            )
            db.add(position)
        
        position.chapter_index = chapter_index
        position.scroll_position = scroll_position
        position.progress_percent = progress_percent
        
        db.commit()
        db.refresh(position)
        
        return position


# Global instance
book_service = BookService()
