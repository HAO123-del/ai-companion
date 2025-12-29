"""
Property-based tests for Companion List and Context Switching
Feature: ai-companion
Property 14: Companion List Consistency
Property 15: Companion Context Switching
Validates: Requirements 10.1, 10.2, 10.4, 10.5
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
TEST_DB_FILE = "test_companion_list_pbt.db"
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

message_content_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz ',
    min_size=1,
    max_size=100
).filter(lambda x: x.strip() != '')


class TestCompanionListConsistency:
    """
    Property 14: Companion List Consistency
    
    For any sequence of companion create/delete operations, the list of companions
    should always reflect the current state accurately - no phantom entries,
    no missing entries, and correct count.
    
    Validates: Requirements 10.1, 10.4, 10.5
    """
    
    @settings(max_examples=50, deadline=None)
    @given(
        companions_data=st.lists(
            st.tuples(companion_name_strategy, companion_personality_strategy),
            min_size=1,
            max_size=10
        ),
        delete_indices=st.lists(st.integers(min_value=0, max_value=9), max_size=5)
    )
    def test_companion_list_after_operations(self, companions_data, delete_indices):
        """
        Property: After any sequence of create/delete operations, list should be consistent.
        Feature: ai-companion, Property 14: Companion List Consistency
        Validates: Requirements 10.1, 10.4, 10.5
        """
        with get_test_db() as db:
            created_ids = []
            
            # Create companions
            for name, personality in companions_data:
                companion = Companion(name=name, personality=personality)
                db.add(companion)
                db.commit()
                db.refresh(companion)
                created_ids.append(companion.id)
            
            # Delete some companions (valid indices only)
            deleted_ids = set()
            for idx in delete_indices:
                if idx < len(created_ids) and created_ids[idx] not in deleted_ids:
                    companion_id = created_ids[idx]
                    companion = db.query(Companion).filter(Companion.id == companion_id).first()
                    if companion:
                        db.delete(companion)
                        db.commit()
                        deleted_ids.add(companion_id)
            
            # Query all companions
            all_companions = db.query(Companion).all()
            remaining_ids = {c.id for c in all_companions}
            
            # Verify consistency
            expected_remaining = set(created_ids) - deleted_ids
            
            # Property 1: Count matches expected
            assert len(all_companions) == len(expected_remaining)
            
            # Property 2: IDs match expected
            assert remaining_ids == expected_remaining
            
            # Property 3: No deleted companions appear in list
            for deleted_id in deleted_ids:
                assert deleted_id not in remaining_ids
            
            # Property 4: All remaining companions have valid data
            for companion in all_companions:
                assert companion.id is not None
                assert companion.name is not None
                assert len(companion.name.strip()) > 0
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_companions=st.integers(min_value=1, max_value=10),
        name_prefix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=10)
    )
    def test_companion_list_ordering(self, num_companions, name_prefix):
        """
        Property: Companion list should maintain consistent ordering by creation time.
        Feature: ai-companion, Property 14: Companion List Consistency
        Validates: Requirements 10.1, 10.4
        """
        with get_test_db() as db:
            created_ids = []
            
            # Create companions in sequence
            for i in range(num_companions):
                companion = Companion(
                    name=f"{name_prefix}_{i}",
                    personality=f"Personality {i}"
                )
                db.add(companion)
                db.commit()
                db.refresh(companion)
                created_ids.append(companion.id)
            
            # Query all companions ordered by created_at
            all_companions = db.query(Companion).order_by(Companion.created_at).all()
            
            # Verify ordering is consistent
            retrieved_ids = [c.id for c in all_companions]
            assert retrieved_ids == created_ids
            
            # Verify created_at timestamps are in order
            for i in range(1, len(all_companions)):
                assert all_companions[i].created_at >= all_companions[i-1].created_at


class TestCompanionContextSwitching:
    """
    Property 15: Companion Context Switching
    
    When switching between companions, the context (messages, settings) should
    correctly reflect the selected companion's data without any cross-contamination.
    
    Validates: Requirements 10.2
    """
    
    @settings(max_examples=50, deadline=None)
    @given(
        num_companions=st.integers(min_value=2, max_value=5),
        messages_per_companion=st.integers(min_value=1, max_value=5),
        switch_sequence=st.lists(st.integers(min_value=0, max_value=4), min_size=3, max_size=10)
    )
    def test_context_switch_message_isolation(self, num_companions, messages_per_companion, switch_sequence):
        """
        Property: Switching companions should always show correct messages for that companion.
        Feature: ai-companion, Property 15: Companion Context Switching
        Validates: Requirements 10.2
        """
        with get_test_db() as db:
            companions = []
            companion_messages = {}
            
            # Create companions with unique messages
            for i in range(num_companions):
                companion = Companion(
                    name=f"Companion_{i}",
                    personality=f"Personality_{i}"
                )
                db.add(companion)
                db.commit()
                db.refresh(companion)
                companions.append(companion)
                
                # Add unique messages for this companion
                messages = []
                for j in range(messages_per_companion):
                    content = f"Message_{i}_{j}_unique"
                    msg = Message(
                        companion_id=companion.id,
                        role='user',
                        content=content
                    )
                    db.add(msg)
                    messages.append(content)
                
                db.commit()
                companion_messages[companion.id] = messages
            
            # Simulate context switching
            for switch_idx in switch_sequence:
                if switch_idx < len(companions):
                    current_companion = companions[switch_idx]
                    
                    # Query messages for current companion (simulating context switch)
                    current_messages = db.query(Message).filter(
                        Message.companion_id == current_companion.id
                    ).all()
                    
                    # Verify correct messages are returned
                    current_contents = {msg.content for msg in current_messages}
                    expected_contents = set(companion_messages[current_companion.id])
                    
                    # Property 1: All expected messages present
                    assert current_contents == expected_contents
                    
                    # Property 2: No messages from other companions
                    for other_id, other_messages in companion_messages.items():
                        if other_id != current_companion.id:
                            for other_msg in other_messages:
                                assert other_msg not in current_contents
    
    @settings(max_examples=50, deadline=None)
    @given(
        companion1_personality=companion_personality_strategy,
        companion2_personality=companion_personality_strategy
    )
    def test_context_switch_settings_isolation(self, companion1_personality, companion2_personality):
        """
        Property: Switching companions should show correct settings for each companion.
        Feature: ai-companion, Property 15: Companion Context Switching
        Validates: Requirements 10.2
        """
        with get_test_db() as db:
            # Create two companions with different settings
            companion1 = Companion(
                name="Companion_A",
                personality=companion1_personality,
                voice_type="preset",
                voice_id="voice_1"
            )
            companion2 = Companion(
                name="Companion_B",
                personality=companion2_personality,
                voice_type="cloned",
                voice_id="voice_2"
            )
            
            db.add(companion1)
            db.add(companion2)
            db.commit()
            db.refresh(companion1)
            db.refresh(companion2)
            
            # Simulate multiple context switches
            for _ in range(5):
                # Switch to companion1
                ctx1 = db.query(Companion).filter(Companion.id == companion1.id).first()
                assert ctx1.personality == companion1_personality
                assert ctx1.voice_type == "preset"
                assert ctx1.voice_id == "voice_1"
                
                # Switch to companion2
                ctx2 = db.query(Companion).filter(Companion.id == companion2.id).first()
                assert ctx2.personality == companion2_personality
                assert ctx2.voice_type == "cloned"
                assert ctx2.voice_id == "voice_2"
                
                # Verify no cross-contamination
                assert ctx1.id != ctx2.id
                assert ctx1.personality != ctx2.personality or companion1_personality == companion2_personality
