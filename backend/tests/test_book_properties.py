"""
Property-based tests for Book Reading
Property 5: Book Content Round-Trip
Property 6: Reading Position Persistence
Validates: Requirements 5.2, 5.5
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, engine


# Test client
client = TestClient(app)


def setup_module(module):
    """Reset database once before all tests"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestBookContentRoundTrip:
    """
    Property 5: Book Content Round-Trip
    For any valid book content, creating and retrieving should
    return the same content.
    
    **Validates: Requirements 5.5**
    """
    
    def test_book_content_preserved(self):
        """
        Feature: ai-companion, Property 5: Book Content Round-Trip
        
        Book content should be preserved exactly after storage.
        """
        test_content = """第一章 开始

这是第一章的内容。
包含多行文本。

第二章 继续

这是第二章的内容。
也有多行。"""
        
        # Create book
        create_response = client.post("/api/books/", json={
            "title": "测试书籍",
            "author": "测试作者",
            "content": test_content
        })
        assert create_response.status_code == 200
        book_id = create_response.json()["id"]
        
        # Retrieve book
        get_response = client.get(f"/api/books/{book_id}")
        assert get_response.status_code == 200
        
        retrieved = get_response.json()
        assert retrieved["content"] == test_content
        assert retrieved["title"] == "测试书籍"
        assert retrieved["author"] == "测试作者"
    
    def test_book_chapters_parsed_correctly(self):
        """
        Feature: ai-companion, Property 5: Book Content Round-Trip
        
        Book chapters should be parsed and retrievable.
        """
        test_content = """第一章 序幕

故事开始了。

第二章 发展

故事继续。

第三章 结局

故事结束。"""
        
        # Create book
        create_response = client.post("/api/books/", json={
            "title": "章节测试",
            "content": test_content
        })
        book_id = create_response.json()["id"]
        
        # Get chapters
        chapters_response = client.get(f"/api/books/{book_id}/chapters")
        assert chapters_response.status_code == 200
        
        chapters = chapters_response.json()
        assert len(chapters) == 3
        assert "第一章" in chapters[0]["title"]
        assert "第二章" in chapters[1]["title"]
        assert "第三章" in chapters[2]["title"]
    
    def test_chapter_content_retrievable(self):
        """
        Feature: ai-companion, Property 5: Book Content Round-Trip
        
        Individual chapter content should be retrievable.
        """
        test_content = """Chapter 1 Introduction

This is the introduction.

Chapter 2 Main Content

This is the main content."""
        
        # Create book
        create_response = client.post("/api/books/", json={
            "title": "English Book",
            "content": test_content
        })
        book_id = create_response.json()["id"]
        
        # Get first chapter
        chapter_response = client.get(f"/api/books/{book_id}/chapters/0")
        assert chapter_response.status_code == 200
        
        chapter = chapter_response.json()
        assert "Chapter 1" in chapter["title"]
        assert "introduction" in chapter["content"].lower()
    
    def test_book_without_chapters(self):
        """
        Feature: ai-companion, Property 5: Book Content Round-Trip
        
        Book without chapter markers should be treated as single chapter.
        """
        test_content = "This is a short story without chapters. Just plain text."
        
        # Create book
        create_response = client.post("/api/books/", json={
            "title": "Short Story",
            "content": test_content
        })
        book_id = create_response.json()["id"]
        
        # Get chapters
        chapters_response = client.get(f"/api/books/{book_id}/chapters")
        chapters = chapters_response.json()
        
        assert len(chapters) == 1
        assert chapters[0]["title"] == "全文"


class TestReadingPositionPersistence:
    """
    Property 6: Reading Position Persistence
    For any reading position update, the position should be
    persisted and retrievable.
    
    **Validates: Requirements 5.2**
    """
    
    def test_reading_position_saved(self):
        """
        Feature: ai-companion, Property 6: Reading Position Persistence
        
        Reading position should be saved and retrievable.
        """
        # Create a book
        book_response = client.post("/api/books/", json={
            "title": "Position Test Book",
            "content": "第一章 开始\n\n内容\n\n第二章 继续\n\n更多内容"
        })
        book_id = book_response.json()["id"]
        
        # Update reading position
        update_response = client.put(f"/api/books/{book_id}/position", json={
            "chapter_index": 1,
            "scroll_position": 150.5
        })
        assert update_response.status_code == 200
        
        # Retrieve position
        get_response = client.get(f"/api/books/{book_id}/position")
        assert get_response.status_code == 200
        
        position = get_response.json()
        assert position["chapter_index"] == 1
        assert position["scroll_position"] == 150.5
    
    def test_reading_position_updates(self):
        """
        Feature: ai-companion, Property 6: Reading Position Persistence
        
        Reading position should update correctly on subsequent saves.
        """
        # Create a book
        book_response = client.post("/api/books/", json={
            "title": "Update Test Book",
            "content": "第一章\n\n内容\n\n第二章\n\n内容\n\n第三章\n\n内容"
        })
        book_id = book_response.json()["id"]
        
        # First update
        client.put(f"/api/books/{book_id}/position", json={
            "chapter_index": 0,
            "scroll_position": 50.0
        })
        
        # Second update
        client.put(f"/api/books/{book_id}/position", json={
            "chapter_index": 2,
            "scroll_position": 200.0
        })
        
        # Verify latest position
        get_response = client.get(f"/api/books/{book_id}/position")
        position = get_response.json()
        
        assert position["chapter_index"] == 2
        assert position["scroll_position"] == 200.0
    
    def test_reading_progress_calculated(self):
        """
        Feature: ai-companion, Property 6: Reading Position Persistence
        
        Reading progress percentage should be calculated correctly.
        """
        # Create a book with 4 chapters
        book_response = client.post("/api/books/", json={
            "title": "Progress Test Book",
            "content": "第一章\n\n1\n\n第二章\n\n2\n\n第三章\n\n3\n\n第四章\n\n4"
        })
        book_id = book_response.json()["id"]
        
        # Update to chapter 2 (index 1, which is 2nd of 4)
        update_response = client.put(f"/api/books/{book_id}/position", json={
            "chapter_index": 1,
            "scroll_position": 0
        })
        
        position = update_response.json()
        # Progress should be (1+1)/4 * 100 = 50%
        assert position["progress_percent"] == 50.0
    
    def test_default_position_for_new_book(self):
        """
        Feature: ai-companion, Property 6: Reading Position Persistence
        
        New book should have default reading position.
        """
        # Create a book
        book_response = client.post("/api/books/", json={
            "title": "New Book",
            "content": "Some content"
        })
        book_id = book_response.json()["id"]
        
        # Get position without setting it
        get_response = client.get(f"/api/books/{book_id}/position")
        assert get_response.status_code == 200
        
        position = get_response.json()
        assert position["chapter_index"] == 0
        assert position["scroll_position"] == 0.0
        assert position["progress_percent"] == 0.0
    
    def test_position_with_companion_id(self):
        """
        Feature: ai-companion, Property 6: Reading Position Persistence
        
        Reading position should be associated with companion.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "ReaderBot",
            "personality": "Bookworm"
        })
        companion_id = companion_response.json()["id"]
        
        # Create a book
        book_response = client.post("/api/books/", json={
            "title": "Companion Book",
            "content": "第一章\n\n内容\n\n第二章\n\n内容"
        })
        book_id = book_response.json()["id"]
        
        # Update position with companion
        client.put(f"/api/books/{book_id}/position", json={
            "chapter_index": 1,
            "scroll_position": 100.0,
            "companion_id": companion_id
        })
        
        # Retrieve with companion
        get_response = client.get(f"/api/books/{book_id}/position?companion_id={companion_id}")
        position = get_response.json()
        
        assert position["chapter_index"] == 1
        assert position["companion_id"] == companion_id
