"""
Property-based tests for Message data model
Feature: ai-companion, Property 2: Message History Persistence
Validates: Requirements 2.3, 2.4
"""
import os
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from backend.database import Base
from backend.models.companion import Companion
from backend.models.message import Message


# Test database setup
TEST_DB_FILE = "test_message_pbt.db"
TEST_DATABASE_URL = f"sqlite:///./{TEST_DB_FILE}"


@contextmanager
def get_test_db():
    """Context manager for test database session"""
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        engine.dispose()
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)


# Strategies for generating valid message data
message_content_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'Z', 'P'),
                           blacklist_characters='\x00'),
    min_size=1, 
    max_size=500
).filter(lambda x: x.strip() != '')

role_strategy = st.sampled_from(['user', 'companion'])

companion_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), 
                           blacklist_characters='\x00'),
    min_size=1, 
    max_size=50
).filter(lambda x: x.strip() != '')


class TestMessageHistoryPersistence:
    """
    Property 2: Message History Persistence
    
    For any sequence of messages sent in a conversation, the message history 
    should be retrievable in the same chronological order, and reopening the 
    app should restore the complete history.
    
    Validates: Requirements 2.3, 2.4
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        companion_name=companion_name_strategy,
        messages=st.lists(
            st.tuples(role_strategy, message_content_strategy),
            min_size=1,
            max_size=10
        )
    )
    def test_message_history_round_trip(self, companion_name, messages):
        """
        Property: For any sequence of messages, save then retrieve should preserve 
        content and chronological order.
        Feature: ai-companion, Property 2: Message History Persistence
        Validates: Requirements 2.3, 2.4
        """
        with get_test_db() as db:
            # Create a companion
            companion = Companion(name=companion_name, personality="Test personality")
            db.add(companion)
            db.commit()
            db.refresh(companion)
            
            # Add messages in order
            for role, content in messages:
                msg = Message(
                    companion_id=companion.id,
                    role=role,
                    content=content
                )
                db.add(msg)
                db.commit()
            
            # Retrieve messages in chronological order
            retrieved = (
                db.query(Message)
                .filter(Message.companion_id == companion.id)
                .order_by(Message.timestamp.asc())
                .all()
            )
            
            # Verify count matches
            assert len(retrieved) == len(messages)
            
            # Verify content and order preserved
            for i, (expected_role, expected_content) in enumerate(messages):
                assert retrieved[i].role == expected_role
                assert retrieved[i].content == expected_content
                assert retrieved[i].companion_id == companion.id
    
    @settings(max_examples=100, deadline=None)
    @given(
        companion_name=companion_name_strategy,
        messages=st.lists(
            st.tuples(role_strategy, message_content_strategy),
            min_size=2,
            max_size=10
        )
    )
    def test_message_timestamps_ordered(self, companion_name, messages):
        """
        Property: Messages should be retrievable in chronological order by timestamp.
        Feature: ai-companion, Property 2: Message History Persistence
        Validates: Requirements 2.3, 2.4
        """
        with get_test_db() as db:
            # Create a companion
            companion = Companion(name=companion_name, personality="Test personality")
            db.add(companion)
            db.commit()
            db.refresh(companion)
            
            # Add messages
            for role, content in messages:
                msg = Message(
                    companion_id=companion.id,
                    role=role,
                    content=content
                )
                db.add(msg)
                db.commit()
            
            # Retrieve messages ordered by timestamp
            retrieved = (
                db.query(Message)
                .filter(Message.companion_id == companion.id)
                .order_by(Message.timestamp.asc())
                .all()
            )
            
            # Verify timestamps are in ascending order
            for i in range(1, len(retrieved)):
                assert retrieved[i].timestamp >= retrieved[i-1].timestamp
