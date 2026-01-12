"""
GameRecord and GameSession models - Game entities
"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from database import Base
import uuid
import json


class GameSession(Base):
    """
    GameSession model representing an active game session.
    
    Attributes:
        id: Unique identifier
        game_id: Game type identifier
        companion_id: Reference to the companion
        state: JSON-encoded game state
        is_active: Whether the session is active
        created_at: Session start timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "game_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String(50), nullable=False)
    companion_id = Column(String(36), ForeignKey("companions.id"), nullable=False)
    state = Column(Text, default="{}")  # JSON state
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def get_state(self):
        """Get parsed state dictionary"""
        try:
            return json.loads(self.state) if self.state else {}
        except:
            return {}
    
    def set_state(self, state_dict):
        """Set state from dictionary"""
        self.state = json.dumps(state_dict, ensure_ascii=False)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "game_id": self.game_id,
            "companion_id": self.companion_id,
            "state": self.get_state(),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class GameRecord(Base):
    """
    GameRecord model representing a completed game record.
    
    Attributes:
        id: Unique identifier
        game_id: Game type identifier
        companion_id: Reference to the companion
        session_id: Reference to the game session
        user_score: User's score
        companion_score: Companion's score
        rounds_played: Number of rounds
        winner: 'user', 'companion', or 'tie'
        played_at: Game timestamp
    """
    __tablename__ = "game_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String(50), nullable=False)
    companion_id = Column(String(36), ForeignKey("companions.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("game_sessions.id"), nullable=True)
    user_score = Column(Integer, default=0)
    companion_score = Column(Integer, default=0)
    rounds_played = Column(Integer, default=0)
    winner = Column(String(20), nullable=True)  # 'user', 'companion', 'tie'
    played_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "game_id": self.game_id,
            "companion_id": self.companion_id,
            "session_id": self.session_id,
            "user_score": self.user_score,
            "companion_score": self.companion_score,
            "rounds_played": self.rounds_played,
            "winner": self.winner,
            "played_at": self.played_at.isoformat() if self.played_at else None
        }
