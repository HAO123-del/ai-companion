"""
Property-based tests for Voice functionality
Feature: ai-companion, Property 7: Voice ID Persistence
Feature: ai-companion, Property 8: Voice Switching
Validates: Requirements 7.2, 7.5
"""
import os
from hypothesis import given, strategies as st, settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from backend.database import Base
from backend.models.companion import Companion


# Test database setup
TEST_DB_FILE = "test_voice_pbt.db"
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


# Strategies
voice_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_',
    min_size=8,
    max_size=50
)

voice_type_strategy = st.sampled_from(['preset', 'cloned'])

companion_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), 
                           blacklist_characters='\x00'),
    min_size=1, 
    max_size=50
).filter(lambda x: x.strip() != '')


class TestVoiceIDPersistence:
    """
    Property 7: Voice ID Persistence
    
    For any successfully cloned voice, the voice ID should be stored 
    and retrievable for future TTS requests.
    
    Validates: Requirements 7.2
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        companion_name=companion_name_strategy,
        voice_id=voice_id_strategy,
        voice_type=voice_type_strategy
    )
    def test_voice_id_persistence(self, companion_name, voice_id, voice_type):
        """
        Property: Voice ID should be persisted and retrievable.
        Feature: ai-companion, Property 7: Voice ID Persistence
        Validates: Requirements 7.2
        """
        with get_test_db() as db:
            # Create companion with voice
            companion = Companion(
                name=companion_name,
                personality="Test personality",
                voice_id=voice_id,
                voice_type=voice_type
            )
            db.add(companion)
            db.commit()
            db.refresh(companion)
            
            saved_id = companion.id
            
            # Retrieve and verify voice ID persisted
            retrieved = db.query(Companion).filter(Companion.id == saved_id).first()
            
            assert retrieved is not None
            assert retrieved.voice_id == voice_id
            assert retrieved.voice_type == voice_type


class TestVoiceSwitching:
    """
    Property 8: Voice Switching
    
    For any Companion with multiple associated voices, switching between 
    voices should correctly update the active voice ID used for TTS.
    
    Validates: Requirements 7.5
    """
    
    @settings(max_examples=100, deadline=None)
    @given(
        companion_name=companion_name_strategy,
        initial_voice_id=voice_id_strategy,
        new_voice_id=voice_id_strategy,
        initial_type=voice_type_strategy,
        new_type=voice_type_strategy
    )
    def test_voice_switching(self, companion_name, initial_voice_id, new_voice_id, initial_type, new_type):
        """
        Property: Switching voices should update the active voice ID.
        Feature: ai-companion, Property 8: Voice Switching
        Validates: Requirements 7.5
        """
        with get_test_db() as db:
            # Create companion with initial voice
            companion = Companion(
                name=companion_name,
                personality="Test personality",
                voice_id=initial_voice_id,
                voice_type=initial_type
            )
            db.add(companion)
            db.commit()
            db.refresh(companion)
            
            saved_id = companion.id
            
            # Verify initial voice
            assert companion.voice_id == initial_voice_id
            assert companion.voice_type == initial_type
            
            # Switch voice
            companion.voice_id = new_voice_id
            companion.voice_type = new_type
            db.commit()
            db.refresh(companion)
            
            # Retrieve and verify voice switched
            retrieved = db.query(Companion).filter(Companion.id == saved_id).first()
            
            assert retrieved is not None
            assert retrieved.voice_id == new_voice_id
            assert retrieved.voice_type == new_type
