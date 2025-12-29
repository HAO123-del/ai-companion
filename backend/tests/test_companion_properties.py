"""
Property-based tests for Companion data model
Feature: ai-companion, Property 1: Companion Data Round-Trip
Validates: Requirements 1.1, 1.3, 1.4
"""
import os
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from backend.database import Base
from backend.models.companion import Companion


# Test database setup
TEST_DB_FILE = "test_companion_pbt.db"
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


# Strategies for generating valid companion data
companion_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), 
                           blacklist_characters='\x00'),
    min_size=1, 
    max_size=50
).filter(lambda x: x.strip() != '')

companion_personality_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'Z'),
                           blacklist_characters='\x00'),
    min_size=1, 
    max_size=200
).filter(lambda x: x.strip() != '')

voice_type_strategy = st.sampled_from(['preset', 'cloned'])

avatar_url_strategy = st.one_of(
    st.none(),
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_./', min_size=5, max_size=100).map(lambda x: f"https://example.com/{x}")
)

voice_id_strategy = st.one_of(
    st.none(),
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=8, max_size=32)
)


class TestCompanionRoundTrip:
    """
    Property 1: Companion Data Round-Trip
    
    For any valid Companion object with name, personality, avatar, and voice settings,
    saving to the database and then retrieving by ID should return an equivalent 
    Companion object with all fields preserved.
    
    Validates: Requirements 1.1, 1.3, 1.4
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        name=companion_name_strategy,
        personality=companion_personality_strategy,
        voice_type=voice_type_strategy,
        avatar_url=avatar_url_strategy,
        voice_id=voice_id_strategy
    )
    def test_companion_database_round_trip(self, name, personality, voice_type, avatar_url, voice_id):
        """
        Property: For any valid companion data, save then retrieve should preserve all fields.
        Feature: ai-companion, Property 1: Companion Data Round-Trip
        Validates: Requirements 1.1, 1.3, 1.4
        """
        with get_test_db() as db:
            # Create companion with all fields
            companion = Companion(
                name=name,
                personality=personality,
                voice_type=voice_type,
                avatar_url=avatar_url,
                voice_id=voice_id
            )
            db.add(companion)
            db.commit()
            db.refresh(companion)
            
            saved_id = companion.id
            
            # Retrieve companion
            retrieved = db.query(Companion).filter(Companion.id == saved_id).first()
            
            # Verify round-trip preserves all data
            assert retrieved is not None
            assert retrieved.name == name
            assert retrieved.personality == personality
            assert retrieved.voice_type == voice_type
            assert retrieved.avatar_url == avatar_url
            assert retrieved.voice_id == voice_id
            assert retrieved.id == saved_id
            assert retrieved.created_at is not None


from backend.models.message import Message


class TestMultiCompanionIsolation:
    """
    Property 13: Multi-Companion Isolation
    
    For any two different Companions, their conversation histories should be 
    completely isolated - messages from one should never appear in the other's history.
    
    Validates: Requirements 10.3
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        name1=companion_name_strategy,
        name2=companion_name_strategy,
        personality1=companion_personality_strategy,
        personality2=companion_personality_strategy,
        messages1=st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=1, max_size=100).filter(lambda x: x.strip() != ''), min_size=1, max_size=5),
        messages2=st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=1, max_size=100).filter(lambda x: x.strip() != ''), min_size=1, max_size=5)
    )
    def test_companion_message_isolation(self, name1, name2, personality1, personality2, messages1, messages2):
        """
        Property: Messages for one companion should never appear in another companion's history.
        Feature: ai-companion, Property 13: Multi-Companion Isolation
        Validates: Requirements 10.3
        """
        with get_test_db() as db:
            # Create two companions
            companion1 = Companion(name=name1, personality=personality1)
            companion2 = Companion(name=name2, personality=personality2)
            db.add(companion1)
            db.add(companion2)
            db.commit()
            db.refresh(companion1)
            db.refresh(companion2)
            
            # Add messages to companion1
            for content in messages1:
                msg = Message(
                    companion_id=companion1.id,
                    role='user',
                    content=content
                )
                db.add(msg)
            
            # Add messages to companion2
            for content in messages2:
                msg = Message(
                    companion_id=companion2.id,
                    role='user',
                    content=content
                )
                db.add(msg)
            
            db.commit()
            
            # Query messages for companion1
            companion1_messages = db.query(Message).filter(
                Message.companion_id == companion1.id
            ).all()
            
            # Query messages for companion2
            companion2_messages = db.query(Message).filter(
                Message.companion_id == companion2.id
            ).all()
            
            # Verify isolation: companion1's messages should only belong to companion1
            for msg in companion1_messages:
                assert msg.companion_id == companion1.id
                assert msg.companion_id != companion2.id
            
            # Verify isolation: companion2's messages should only belong to companion2
            for msg in companion2_messages:
                assert msg.companion_id == companion2.id
                assert msg.companion_id != companion1.id
            
            # Verify message counts match what we added
            assert len(companion1_messages) == len(messages1)
            assert len(companion2_messages) == len(messages2)
            
            # Verify content isolation - no message content from one appears in the other
            companion1_contents = {msg.content for msg in companion1_messages}
            companion2_contents = {msg.content for msg in companion2_messages}
            
            # Each companion should have exactly their own messages
            assert companion1_contents == set(messages1)
            assert companion2_contents == set(messages2)
