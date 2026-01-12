"""
Tests for database connection and basic operations
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.models import Companion, Message


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_database_connection(test_db):
    """Test that database connection works"""
    from sqlalchemy import text
    # Simple query to verify connection
    result = test_db.execute(text("SELECT 1")).fetchone()
    assert result[0] == 1


def test_create_companion(test_db):
    """Test creating a companion in the database"""
    companion = Companion(
        name="Test Companion",
        personality="Friendly and helpful",
        voice_type="preset"
    )
    test_db.add(companion)
    test_db.commit()
    test_db.refresh(companion)
    
    assert companion.id is not None
    assert companion.name == "Test Companion"
    assert companion.personality == "Friendly and helpful"


def test_create_message(test_db):
    """Test creating a message linked to a companion"""
    # First create a companion
    companion = Companion(
        name="Test Companion",
        personality="Friendly"
    )
    test_db.add(companion)
    test_db.commit()
    test_db.refresh(companion)
    
    # Then create a message
    message = Message(
        companion_id=companion.id,
        role="user",
        content="Hello!"
    )
    test_db.add(message)
    test_db.commit()
    test_db.refresh(message)
    
    assert message.id is not None
    assert message.companion_id == companion.id
    assert message.content == "Hello!"


def test_get_db_dependency():
    """Test that get_db dependency yields a session"""
    gen = get_db()
    db = next(gen)
    assert db is not None
    # Clean up
    try:
        next(gen)
    except StopIteration:
        pass
