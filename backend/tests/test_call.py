"""
Tests for Call Service - Call state transitions
Tests connecting -> active -> ended state flow
"""
import pytest
from backend.services.call_service import CallService, CallStatus, CallSession


class TestCallStateTransitions:
    """Test call state transitions: connecting -> active -> ended"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.call_service = CallService()
    
    def test_create_session_starts_in_connecting(self):
        """Test that new sessions start in connecting state"""
        session = self.call_service.create_session(
            companion_id="test-companion",
            companion_name="Test",
            personality="friendly",
            voice_id="female-shaonv"
        )
        
        assert session.status == CallStatus.CONNECTING
        assert session.companion_id == "test-companion"
        assert session.id is not None
    
    def test_activate_session_transitions_to_active(self):
        """Test connecting -> active transition"""
        session = self.call_service.create_session(
            companion_id="test-companion",
            companion_name="Test",
            personality="friendly",
            voice_id="female-shaonv"
        )
        
        assert session.status == CallStatus.CONNECTING
        
        # Activate
        result = self.call_service.activate_session(session.id)
        
        assert result is True
        assert session.status == CallStatus.ACTIVE
    
    def test_end_session_transitions_to_ended(self):
        """Test active -> ended transition"""
        session = self.call_service.create_session(
            companion_id="test-companion",
            companion_name="Test",
            personality="friendly",
            voice_id="female-shaonv"
        )
        
        # Activate first
        self.call_service.activate_session(session.id)
        assert session.status == CallStatus.ACTIVE
        
        # End
        result = self.call_service.end_session(session.id)
        
        assert result is True
        # Session should be removed from active sessions
        assert self.call_service.get_session(session.id) is None
    
    def test_cannot_activate_nonexistent_session(self):
        """Test activating non-existent session fails"""
        result = self.call_service.activate_session("nonexistent-id")
        assert result is False
    
    def test_cannot_end_nonexistent_session(self):
        """Test ending non-existent session fails"""
        result = self.call_service.end_session("nonexistent-id")
        assert result is False
    
    def test_cannot_activate_already_active_session(self):
        """Test that activating an already active session returns False"""
        session = self.call_service.create_session(
            companion_id="test-companion",
            companion_name="Test",
            personality="friendly",
            voice_id="female-shaonv"
        )
        
        # First activation
        self.call_service.activate_session(session.id)
        
        # Second activation should fail
        result = self.call_service.activate_session(session.id)
        assert result is False
    
    def test_full_state_flow(self):
        """Test complete state flow: connecting -> active -> ended"""
        # Create (connecting)
        session = self.call_service.create_session(
            companion_id="test-companion",
            companion_name="Test",
            personality="friendly",
            voice_id="female-shaonv"
        )
        assert session.status == CallStatus.CONNECTING
        
        # Activate
        self.call_service.activate_session(session.id)
        assert session.status == CallStatus.ACTIVE
        
        # End
        session_id = session.id
        self.call_service.end_session(session_id)
        
        # Session should be removed
        assert self.call_service.get_session(session_id) is None
    
    def test_session_to_dict(self):
        """Test session serialization"""
        session = self.call_service.create_session(
            companion_id="test-companion",
            companion_name="Test",
            personality="friendly",
            voice_id="female-shaonv"
        )
        
        data = session.to_dict()
        
        assert data["id"] == session.id
        assert data["companion_id"] == "test-companion"
        assert data["status"] == "connecting"
        assert "start_time" in data
        assert "duration" in data
    
    def test_session_duration(self):
        """Test session duration calculation"""
        session = self.call_service.create_session(
            companion_id="test-companion",
            companion_name="Test",
            personality="friendly",
            voice_id="female-shaonv"
        )
        
        # Duration should be 0 or very small for new session
        assert session.get_duration() >= 0
    
    def test_multiple_sessions(self):
        """Test managing multiple concurrent sessions"""
        session1 = self.call_service.create_session(
            companion_id="companion-1",
            companion_name="Test1",
            personality="friendly",
            voice_id="female-shaonv"
        )
        
        session2 = self.call_service.create_session(
            companion_id="companion-2",
            companion_name="Test2",
            personality="calm",
            voice_id="male-qn-qingse"
        )
        
        assert self.call_service.get_active_sessions_count() == 2
        
        # End one session
        self.call_service.end_session(session1.id)
        assert self.call_service.get_active_sessions_count() == 1
        
        # End second session
        self.call_service.end_session(session2.id)
        assert self.call_service.get_active_sessions_count() == 0
