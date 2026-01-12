"""
Call Service - WebSocket-based Voice Call Integration
Handles real-time voice communication with AI companion
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable, Any
from enum import Enum

from services.chat_service import chat_service
from services.voice_service import voice_service


class CallStatus(str, Enum):
    """Call session status"""
    CONNECTING = "connecting"
    ACTIVE = "active"
    ENDED = "ended"


class CallSession:
    """Represents an active call session"""
    
    def __init__(self, companion_id: str, companion_name: str, personality: str, voice_id: str):
        self.id = str(uuid.uuid4())
        self.companion_id = companion_id
        self.companion_name = companion_name
        self.personality = personality
        self.voice_id = voice_id
        self.start_time = datetime.utcnow()
        self.status = CallStatus.CONNECTING
        self.conversation_history: list = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "companion_id": self.companion_id,
            "start_time": self.start_time.isoformat(),
            "status": self.status.value,
            "duration": self.get_duration()
        }
    
    def get_duration(self) -> int:
        """Get call duration in seconds"""
        if self.status == CallStatus.ENDED:
            return 0
        return int((datetime.utcnow() - self.start_time).total_seconds())
    
    def activate(self):
        """Transition to active state"""
        if self.status == CallStatus.CONNECTING:
            self.status = CallStatus.ACTIVE
    
    def end(self):
        """End the call session"""
        self.status = CallStatus.ENDED


class CallService:
    """
    Service for managing voice call sessions.
    Coordinates between speech recognition, chat, and TTS.
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, CallSession] = {}
    
    def create_session(
        self, 
        companion_id: str, 
        companion_name: str, 
        personality: str,
        voice_id: str
    ) -> CallSession:
        """
        Create a new call session.
        
        Args:
            companion_id: ID of the companion
            companion_name: Name of the companion
            personality: Personality description
            voice_id: Voice ID for TTS
            
        Returns:
            New CallSession instance
        """
        session = CallSession(companion_id, companion_name, personality, voice_id)
        self.active_sessions[session.id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[CallSession]:
        """Get a session by ID"""
        return self.active_sessions.get(session_id)
    
    def activate_session(self, session_id: str) -> bool:
        """Activate a connecting session"""
        session = self.get_session(session_id)
        if session and session.status == CallStatus.CONNECTING:
            session.activate()
            return True
        return False
    
    def end_session(self, session_id: str) -> bool:
        """End a call session"""
        session = self.get_session(session_id)
        if session:
            session.end()
            # Remove from active sessions
            del self.active_sessions[session_id]
            return True
        return False
    
    async def process_user_speech(
        self, 
        session_id: str, 
        text: str,
        api_key: str = None,
        group_id: str = None
    ) -> Dict[str, Any]:
        """
        Process user speech text and generate AI response with audio.
        
        Args:
            session_id: Call session ID
            text: Transcribed user speech
            api_key: MiniMax API key
            group_id: MiniMax group ID
            
        Returns:
            Dict with response text and audio data
        """
        session = self.get_session(session_id)
        if not session or session.status != CallStatus.ACTIVE:
            return {"error": "Invalid or inactive session"}
        
        # Add user message to history
        session.conversation_history.append({
            "role": "user",
            "content": text
        })
        
        # Create chat service with API key
        from services.chat_service import ChatService
        chat_svc = ChatService(api_key=api_key, group_id=group_id)
        
        # Get AI response
        response_text = await chat_svc.send_message(
            user_message=text,
            companion_name=session.companion_name,
            personality=session.personality,
            history=session.conversation_history
        )
        
        # Add AI response to history
        session.conversation_history.append({
            "role": "companion",
            "content": response_text
        })
        
        # Generate TTS audio with API credentials
        from services.voice_service import VoiceService
        tts_result = {"success": False}
        try:
            voice_svc = VoiceService(api_key=api_key, group_id=group_id)
            tts_result = await voice_svc.synthesize_speech(
                text=response_text,
                voice_id=session.voice_id
            )
            print(f"TTS Result: success={tts_result.get('success')}, error={tts_result.get('error')}")
        except Exception as e:
            print(f"TTS Error: {e}")
        
        return {
            "text": response_text,
            "audio": tts_result.get("audio") if tts_result.get("success") else None,
            "audio_format": tts_result.get("format", "mp3")
        }
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.active_sessions)
    
    def cleanup_stale_sessions(self, max_duration_seconds: int = 3600):
        """Remove sessions that have been active too long"""
        stale_ids = []
        for session_id, session in self.active_sessions.items():
            if session.get_duration() > max_duration_seconds:
                stale_ids.append(session_id)
        
        for session_id in stale_ids:
            self.end_session(session_id)
        
        return len(stale_ids)


# Global instance
call_service = CallService()
