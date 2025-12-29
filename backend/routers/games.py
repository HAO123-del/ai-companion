"""
Games API Router - Game management and gameplay operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from database import get_db
from models.game import GameSession, GameRecord
from services.game_service import game_service

router = APIRouter()


class SessionCreate(BaseModel):
    """Schema for creating a game session"""
    game_id: str
    companion_id: str


class WordChainPlay(BaseModel):
    """Schema for word chain play"""
    word: str


class TriviaAnswer(BaseModel):
    """Schema for trivia answer"""
    answer: str


class GuessNumberPlay(BaseModel):
    """Schema for guess number play"""
    guess: int


# Game listing
@router.get("/")
async def list_games():
    """List all available games"""
    return game_service.get_available_games()


# Records and statistics - MUST be before /{game_id} to avoid route conflicts
@router.get("/records")
async def list_game_records(
    companion_id: str = Query(..., description="Companion ID"),
    game_id: Optional[str] = Query(None, description="Game ID filter"),
    limit: int = Query(20, description="Maximum records"),
    db: Session = Depends(get_db)
):
    """List game records for a companion"""
    query = db.query(GameRecord).filter(GameRecord.companion_id == companion_id)
    if game_id:
        query = query.filter(GameRecord.game_id == game_id)
    
    records = query.order_by(GameRecord.played_at.desc()).limit(limit).all()
    return [r.to_dict() for r in records]


@router.get("/stats")
async def get_game_stats(
    companion_id: str = Query(..., description="Companion ID"),
    db: Session = Depends(get_db)
):
    """Get game statistics for a companion"""
    return game_service.get_statistics(db, companion_id)


@router.get("/{game_id}")
async def get_game_info(game_id: str):
    """Get information about a specific game"""
    info = game_service.get_game_info(game_id)
    if not info:
        raise HTTPException(status_code=404, detail="Game not found")
    return info


# Session management
@router.post("/sessions")
async def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    """Create a new game session"""
    # Check for existing active session
    existing = game_service.get_active_session(db, data.companion_id, data.game_id)
    if existing:
        return existing.to_dict()
    
    session = game_service.create_session(db, data.game_id, data.companion_id)
    return session.to_dict()


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get a game session"""
    session = game_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.get("/sessions/active/{companion_id}")
async def get_active_sessions(companion_id: str, db: Session = Depends(get_db)):
    """Get all active sessions for a companion"""
    sessions = (
        db.query(GameSession)
        .filter(
            GameSession.companion_id == companion_id,
            GameSession.is_active == True
        )
        .all()
    )
    return [s.to_dict() for s in sessions]


@router.post("/sessions/{session_id}/end")
async def end_session(session_id: str, db: Session = Depends(get_db)):
    """End a game session"""
    result = game_service.end_session(db, session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


# Game-specific play endpoints
@router.post("/sessions/{session_id}/word-chain")
async def play_word_chain(
    session_id: str,
    data: WordChainPlay,
    db: Session = Depends(get_db)
):
    """Play a word in word chain game"""
    result = game_service.play_word_chain(db, session_id, data.word)
    if "error" in result and not result.get("valid", True):
        return result  # Return validation errors normally
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/sessions/{session_id}/trivia")
async def play_trivia(
    session_id: str,
    data: TriviaAnswer,
    db: Session = Depends(get_db)
):
    """Answer a trivia question"""
    result = game_service.play_trivia(db, session_id, data.answer)
    if "error" in result and not result.get("finished"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/sessions/{session_id}/guess-number")
async def play_guess_number(
    session_id: str,
    data: GuessNumberPlay,
    db: Session = Depends(get_db)
):
    """Make a guess in guess number game"""
    result = game_service.play_guess_number(db, session_id, data.guess)
    if "error" in result and not result.get("finished"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result
