# -*- coding: utf-8 -*-
"""
Game Service - Game session and state management
Handles game sessions, state transitions, and scoring
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import random

from models.game import GameSession, GameRecord


# Available games configuration
AVAILABLE_GAMES = {
    "word_chain": {
        "id": "word_chain",
        "name": "成语接龙",
        "type": "word",
        "description": "接龙游戏，考验词汇量",
        "rules": "用上一个成语的最后一个字作为下一个成语的开头"
    },
    "trivia": {
        "id": "trivia",
        "name": "知识问答",
        "type": "trivia",
        "description": "趣味问答，增长知识",
        "rules": "回答问题，答对得分"
    },
    "guess_number": {
        "id": "guess_number",
        "name": "猜数字",
        "type": "logic",
        "description": "猜测数字，锻炼逻辑",
        "rules": "猜测1-100之间的数字，根据提示缩小范围"
    }
}

# Sample trivia questions
TRIVIA_QUESTIONS = [
    {"question": "地球上最大的海洋是什么？", "answer": "太平洋", "options": ["太平洋", "大西洋", "印度洋", "北冰洋"]},
    {"question": "光的速度大约是多少？", "answer": "30万公里/秒", "options": ["30万公里/秒", "3万公里/秒", "300万公里/秒", "3000公里/秒"]},
    {"question": "中国最长的河流是什么？", "answer": "长江", "options": ["黄河", "长江", "珠江", "淮河"]},
    {"question": "一年有多少天？", "answer": "365天", "options": ["360天", "365天", "366天", "364天"]},
    {"question": "水的化学式是什么？", "answer": "H2O", "options": ["H2O", "CO2", "O2", "NaCl"]},
]


class GameService:
    """Service for managing game sessions and state."""
    
    def get_available_games(self) -> List[Dict[str, Any]]:
        """Get list of available games"""
        return list(AVAILABLE_GAMES.values())
    
    def get_game_info(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific game"""
        return AVAILABLE_GAMES.get(game_id)
    
    def create_session(self, db: Session, game_id: str, companion_id: str) -> GameSession:
        """Create a new game session."""
        initial_state = self._get_initial_state(game_id)
        
        session = GameSession(
            game_id=game_id,
            companion_id=companion_id,
            is_active=True
        )
        session.set_state(initial_state)
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    def _get_initial_state(self, game_id: str) -> Dict[str, Any]:
        """Get initial state for a game type"""
        if game_id == "word_chain":
            return {
                "current_word": None,
                "words_used": [],
                "user_score": 0,
                "companion_score": 0,
                "turn": "user",
                "rounds": 0
            }
        elif game_id == "trivia":
            questions = random.sample(TRIVIA_QUESTIONS, min(5, len(TRIVIA_QUESTIONS)))
            return {
                "questions": questions,
                "current_index": 0,
                "user_score": 0,
                "companion_score": 0,
                "answers": []
            }
        elif game_id == "guess_number":
            target = random.randint(1, 100)
            return {
                "target": target,
                "min_range": 1,
                "max_range": 100,
                "guesses": [],
                "max_guesses": 7,
                "won": False
            }
        return {}
    
    def get_session(self, db: Session, session_id: str) -> Optional[GameSession]:
        """Get a game session by ID"""
        return db.query(GameSession).filter(GameSession.id == session_id).first()
    
    def get_active_session(self, db: Session, companion_id: str, game_id: str) -> Optional[GameSession]:
        """Get active session for a companion and game"""
        return (
            db.query(GameSession)
            .filter(
                GameSession.companion_id == companion_id,
                GameSession.game_id == game_id,
                GameSession.is_active == True
            )
            .first()
        )
    
    def update_session_state(self, db: Session, session_id: str, new_state: Dict[str, Any]) -> Optional[GameSession]:
        """Update session state"""
        session = self.get_session(db, session_id)
        if not session:
            return None
        
        session.set_state(new_state)
        db.commit()
        db.refresh(session)
        
        return session
    
    def end_session(self, db: Session, session_id: str) -> Optional[Dict[str, Any]]:
        """End a game session and create a record."""
        session = self.get_session(db, session_id)
        if not session:
            return None
        
        state = session.get_state()
        user_score = state.get("user_score", 0)
        companion_score = state.get("companion_score", 0)
        
        if user_score > companion_score:
            winner = "user"
        elif companion_score > user_score:
            winner = "companion"
        else:
            winner = "tie"
        
        record = GameRecord(
            game_id=session.game_id,
            companion_id=session.companion_id,
            session_id=session.id,
            user_score=user_score,
            companion_score=companion_score,
            rounds_played=state.get("rounds", state.get("current_index", 0)),
            winner=winner
        )
        
        db.add(record)
        session.is_active = False
        db.commit()
        db.refresh(record)
        
        return record.to_dict()

    def play_word_chain(self, db: Session, session_id: str, word: str) -> Dict[str, Any]:
        """Play a word in word chain game."""
        session = self.get_session(db, session_id)
        if not session or session.game_id != "word_chain":
            return {"error": "Invalid session"}
        
        state = session.get_state()
        
        if word in state.get("words_used", []):
            return {"error": "这个词已经用过了", "valid": False}
        
        current_word = state.get("current_word")
        if current_word and word[0] != current_word[-1]:
            return {"error": f"需要以'{current_word[-1]}'开头", "valid": False}
        
        state["words_used"].append(word)
        state["current_word"] = word
        state["user_score"] = state.get("user_score", 0) + 1
        state["rounds"] = state.get("rounds", 0) + 1
        state["turn"] = "companion"
        
        session.set_state(state)
        db.commit()
        
        return {"valid": True, "word": word, "state": state}
    
    def play_trivia(self, db: Session, session_id: str, answer: str) -> Dict[str, Any]:
        """Answer a trivia question."""
        session = self.get_session(db, session_id)
        if not session or session.game_id != "trivia":
            return {"error": "Invalid session"}
        
        state = session.get_state()
        questions = state.get("questions", [])
        current_index = state.get("current_index", 0)
        
        if current_index >= len(questions):
            return {"error": "No more questions", "finished": True}
        
        current_question = questions[current_index]
        correct = answer == current_question["answer"]
        
        if correct:
            state["user_score"] = state.get("user_score", 0) + 1
        
        state["answers"].append({
            "question": current_question["question"],
            "user_answer": answer,
            "correct_answer": current_question["answer"],
            "correct": correct
        })
        state["current_index"] = current_index + 1
        
        session.set_state(state)
        db.commit()
        
        finished = state["current_index"] >= len(questions)
        
        return {
            "correct": correct,
            "correct_answer": current_question["answer"],
            "finished": finished,
            "state": state
        }
    
    def play_guess_number(self, db: Session, session_id: str, guess: int) -> Dict[str, Any]:
        """Make a guess in guess number game."""
        session = self.get_session(db, session_id)
        if not session or session.game_id != "guess_number":
            return {"error": "Invalid session"}
        
        state = session.get_state()
        target = state.get("target")
        guesses = state.get("guesses", [])
        max_guesses = state.get("max_guesses", 7)
        
        if state.get("won") or len(guesses) >= max_guesses:
            return {"error": "Game already finished", "finished": True}
        
        guesses.append(guess)
        state["guesses"] = guesses
        
        if guess == target:
            state["won"] = True
            state["user_score"] = max_guesses - len(guesses) + 1
            hint = "correct"
        elif guess < target:
            state["min_range"] = max(state.get("min_range", 1), guess + 1)
            hint = "higher"
        else:
            state["max_range"] = min(state.get("max_range", 100), guess - 1)
            hint = "lower"
        
        session.set_state(state)
        db.commit()
        
        finished = state["won"] or len(guesses) >= max_guesses
        
        return {
            "guess": guess,
            "hint": hint,
            "finished": finished,
            "won": state["won"],
            "target": target if finished else None,
            "state": state
        }
    
    def get_statistics(self, db: Session, companion_id: str) -> Dict[str, Any]:
        """Get game statistics for a companion"""
        records = db.query(GameRecord).filter(GameRecord.companion_id == companion_id).all()
        
        if not records:
            return {
                "total_games": 0,
                "total_user_score": 0,
                "total_companion_score": 0,
                "wins": 0,
                "losses": 0,
                "ties": 0,
                "games_by_type": {}
            }
        
        stats = {
            "total_games": len(records),
            "total_user_score": 0,
            "total_companion_score": 0,
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "games_by_type": {}
        }
        
        for r in records:
            stats["total_user_score"] += r.user_score or 0
            stats["total_companion_score"] += r.companion_score or 0
            
            if r.winner == "user":
                stats["wins"] += 1
            elif r.winner == "companion":
                stats["losses"] += 1
            else:
                stats["ties"] += 1
            
            if r.game_id not in stats["games_by_type"]:
                stats["games_by_type"][r.game_id] = {"played": 0, "wins": 0}
            
            stats["games_by_type"][r.game_id]["played"] += 1
            if r.winner == "user":
                stats["games_by_type"][r.game_id]["wins"] += 1
        
        return stats


# Global instance
game_service = GameService()
