"""
Tests for API routes
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.database import Base, get_db


# Use file-based SQLite for testing (avoids Windows threading issues)
TEST_DB_FILE = "test_ai_companion.db"
TEST_DATABASE_URL = f"sqlite:///./{TEST_DB_FILE}"


@pytest.fixture
def test_client():
    """Create a test client with test database"""
    # Remove old test db if exists
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()
    engine.dispose()
    
    # Clean up test db file
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


def test_root_endpoint(test_client):
    """Test the root health check endpoint"""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_endpoint(test_client):
    """Test the health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_create_companion_api(test_client):
    """Test creating a companion via API"""
    response = test_client.post("/api/companions/", json={
        "name": "Eve",
        "personality": "Friendly and curious",
        "voice_type": "preset"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Eve"
    assert data["personality"] == "Friendly and curious"
    assert "id" in data


def test_list_companions_api(test_client):
    """Test listing companions via API"""
    # Create a companion first
    test_client.post("/api/companions/", json={
        "name": "Eve",
        "personality": "Friendly"
    })
    
    response = test_client.get("/api/companions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_companion_api(test_client):
    """Test getting a specific companion by ID"""
    # Create a companion first
    create_response = test_client.post("/api/companions/", json={
        "name": "Luna",
        "personality": "Calm and thoughtful"
    })
    companion_id = create_response.json()["id"]
    
    # Get the companion
    response = test_client.get(f"/api/companions/{companion_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == companion_id
    assert data["name"] == "Luna"


def test_get_companion_not_found(test_client):
    """Test getting a non-existent companion returns 404"""
    response = test_client.get("/api/companions/non-existent-id")
    assert response.status_code == 404


def test_update_companion_api(test_client):
    """Test updating a companion via API"""
    # Create a companion first
    create_response = test_client.post("/api/companions/", json={
        "name": "Original Name",
        "personality": "Original personality"
    })
    companion_id = create_response.json()["id"]
    
    # Update the companion
    response = test_client.put(f"/api/companions/{companion_id}", json={
        "name": "Updated Name",
        "personality": "Updated personality"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["personality"] == "Updated personality"


def test_delete_companion_api(test_client):
    """Test deleting a companion via API"""
    # Create a companion first
    create_response = test_client.post("/api/companions/", json={
        "name": "ToDelete",
        "personality": "Will be deleted"
    })
    companion_id = create_response.json()["id"]
    
    # Delete the companion
    response = test_client.delete(f"/api/companions/{companion_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = test_client.get(f"/api/companions/{companion_id}")
    assert get_response.status_code == 404


def test_list_games_api(test_client):
    """Test listing available games"""
    response = test_client.get("/api/games/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(g["id"] == "word_chain" for g in data)


# Voice API Tests
def test_get_preset_voices(test_client):
    """Test getting preset voices list"""
    response = test_client.get("/api/voice/presets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all("id" in v and "name" in v for v in data)


def test_update_companion_voice(test_client):
    """Test updating companion voice setting"""
    # Create a companion first
    companion_response = test_client.post("/api/companions/", json={
        "name": "VoiceTest",
        "personality": "Test"
    })
    companion_id = companion_response.json()["id"]
    
    # Update voice
    response = test_client.put(
        f"/api/voice/companion/{companion_id}/voice?voice_id=female-shaonv&voice_type=preset"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["voice_id"] == "female-shaonv"
    assert data["voice_type"] == "preset"


# Message API Tests
def test_create_message_api(test_client):
    """Test creating a message via API"""
    # Create a companion first
    companion_response = test_client.post("/api/companions/", json={
        "name": "ChatBot",
        "personality": "Helpful"
    })
    companion_id = companion_response.json()["id"]
    
    # Create a message
    response = test_client.post("/api/messages/", json={
        "companion_id": companion_id,
        "role": "user",
        "content": "Hello!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["companion_id"] == companion_id
    assert data["role"] == "user"
    assert data["content"] == "Hello!"


def test_list_messages_api(test_client):
    """Test listing messages for a companion"""
    # Create a companion
    companion_response = test_client.post("/api/companions/", json={
        "name": "ChatBot",
        "personality": "Helpful"
    })
    companion_id = companion_response.json()["id"]
    
    # Create messages
    test_client.post("/api/messages/", json={
        "companion_id": companion_id,
        "role": "user",
        "content": "Hello!"
    })
    test_client.post("/api/messages/", json={
        "companion_id": companion_id,
        "role": "companion",
        "content": "Hi there!"
    })
    
    # List messages
    response = test_client.get(f"/api/messages/?companion_id={companion_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_clear_message_history_api(test_client):
    """Test clearing message history for a companion"""
    # Create a companion
    companion_response = test_client.post("/api/companions/", json={
        "name": "ChatBot",
        "personality": "Helpful"
    })
    companion_id = companion_response.json()["id"]
    
    # Create a message
    test_client.post("/api/messages/", json={
        "companion_id": companion_id,
        "role": "user",
        "content": "Hello!"
    })
    
    # Clear history
    response = test_client.delete(f"/api/messages/companion/{companion_id}")
    assert response.status_code == 200
    
    # Verify cleared
    list_response = test_client.get(f"/api/messages/?companion_id={companion_id}")
    assert len(list_response.json()) == 0


# Memory API Tests
def test_create_memory_api(test_client):
    """Test creating a memory via API"""
    # Create a companion first
    companion_response = test_client.post("/api/companions/", json={
        "name": "MemoryBot",
        "personality": "Remembers everything"
    })
    companion_id = companion_response.json()["id"]
    
    # Create a memory
    response = test_client.post("/api/memories/", json={
        "companion_id": companion_id,
        "category": "preference",
        "content": "User likes coffee",
        "importance": 0.8
    })
    assert response.status_code == 200
    data = response.json()
    assert data["companion_id"] == companion_id
    assert data["category"] == "preference"
    assert data["content"] == "User likes coffee"
    assert data["importance"] == 0.8


def test_list_memories_api(test_client):
    """Test listing memories for a companion"""
    # Create a companion
    companion_response = test_client.post("/api/companions/", json={
        "name": "MemoryBot",
        "personality": "Remembers everything"
    })
    companion_id = companion_response.json()["id"]
    
    # Create memories with different importance
    test_client.post("/api/memories/", json={
        "companion_id": companion_id,
        "category": "preference",
        "content": "Low importance memory",
        "importance": 0.3
    })
    test_client.post("/api/memories/", json={
        "companion_id": companion_id,
        "category": "fact",
        "content": "High importance memory",
        "importance": 0.9
    })
    
    # List memories (should be sorted by importance desc)
    response = test_client.get(f"/api/memories/?companion_id={companion_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # First memory should have higher importance
    assert data[0]["importance"] >= data[1]["importance"]


def test_update_memory_api(test_client):
    """Test updating a memory via API"""
    # Create a companion
    companion_response = test_client.post("/api/companions/", json={
        "name": "MemoryBot",
        "personality": "Remembers everything"
    })
    companion_id = companion_response.json()["id"]
    
    # Create a memory
    create_response = test_client.post("/api/memories/", json={
        "companion_id": companion_id,
        "category": "preference",
        "content": "Original content",
        "importance": 0.5
    })
    memory_id = create_response.json()["id"]
    
    # Update the memory
    response = test_client.put(f"/api/memories/{memory_id}", json={
        "content": "Updated content",
        "importance": 0.9
    })
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated content"
    assert data["importance"] == 0.9


def test_delete_memory_api(test_client):
    """Test deleting a memory via API"""
    # Create a companion
    companion_response = test_client.post("/api/companions/", json={
        "name": "MemoryBot",
        "personality": "Remembers everything"
    })
    companion_id = companion_response.json()["id"]
    
    # Create a memory
    create_response = test_client.post("/api/memories/", json={
        "companion_id": companion_id,
        "category": "fact",
        "content": "To be deleted"
    })
    memory_id = create_response.json()["id"]
    
    # Delete the memory
    response = test_client.delete(f"/api/memories/{memory_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = test_client.get(f"/api/memories/{memory_id}")
    assert get_response.status_code == 404


def test_get_relevant_memories_api(test_client):
    """Test getting relevant memories based on context"""
    # Create a companion
    companion_response = test_client.post("/api/companions/", json={
        "name": "MemoryBot",
        "personality": "Remembers everything"
    })
    companion_id = companion_response.json()["id"]
    
    # Create memories
    test_client.post("/api/memories/", json={
        "companion_id": companion_id,
        "category": "preference",
        "content": "User loves coffee and tea",
        "importance": 0.8
    })
    test_client.post("/api/memories/", json={
        "companion_id": companion_id,
        "category": "fact",
        "content": "User works as a programmer",
        "importance": 0.7
    })
    
    # Get relevant memories for coffee context
    response = test_client.get(
        f"/api/memories/relevant?companion_id={companion_id}&context=coffee"
    )
    assert response.status_code == 200
    data = response.json()
    # Should return the coffee-related memory
    assert len(data) >= 1
    assert any("coffee" in m["content"].lower() for m in data)



# Reminder API Tests
def test_create_reminder_api(test_client):
    """Test creating a reminder via API"""
    # Create a companion first
    companion_response = test_client.post("/api/companions/", json={
        "name": "ReminderBot",
        "personality": "Helpful"
    })
    companion_id = companion_response.json()["id"]
    
    # Create a reminder
    response = test_client.post("/api/reminders/", json={
        "companion_id": companion_id,
        "type": "scheduled",
        "message": "Time to take a break!",
        "enabled": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["companion_id"] == companion_id
    assert data["type"] == "scheduled"
    assert data["message"] == "Time to take a break!"
    assert data["enabled"] == True


def test_list_reminders_api(test_client):
    """Test listing reminders for a companion"""
    # Create a companion
    companion_response = test_client.post("/api/companions/", json={
        "name": "ReminderBot",
        "personality": "Helpful"
    })
    companion_id = companion_response.json()["id"]
    
    # Create reminders
    test_client.post("/api/reminders/", json={
        "companion_id": companion_id,
        "type": "greeting",
        "message": "Good morning!"
    })
    test_client.post("/api/reminders/", json={
        "companion_id": companion_id,
        "type": "checkin",
        "message": "How are you doing?"
    })
    
    # List reminders
    response = test_client.get(f"/api/reminders/?companion_id={companion_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_update_reminder_api(test_client):
    """Test updating a reminder via API"""
    # Create a companion
    companion_response = test_client.post("/api/companions/", json={
        "name": "ReminderBot",
        "personality": "Helpful"
    })
    companion_id = companion_response.json()["id"]
    
    # Create a reminder
    create_response = test_client.post("/api/reminders/", json={
        "companion_id": companion_id,
        "type": "scheduled",
        "message": "Original message",
        "enabled": True
    })
    reminder_id = create_response.json()["id"]
    
    # Update the reminder
    response = test_client.put(f"/api/reminders/{reminder_id}", json={
        "message": "Updated message",
        "enabled": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Updated message"
    assert data["enabled"] == False


def test_delete_reminder_api(test_client):
    """Test deleting a reminder via API"""
    # Create a companion
    companion_response = test_client.post("/api/companions/", json={
        "name": "ReminderBot",
        "personality": "Helpful"
    })
    companion_id = companion_response.json()["id"]
    
    # Create a reminder
    create_response = test_client.post("/api/reminders/", json={
        "companion_id": companion_id,
        "type": "scheduled",
        "message": "To be deleted"
    })
    reminder_id = create_response.json()["id"]
    
    # Delete the reminder
    response = test_client.delete(f"/api/reminders/{reminder_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = test_client.get(f"/api/reminders/{reminder_id}")
    assert get_response.status_code == 404
