"""
Property-based tests for Game System
Property 17: Game Session State
Property 18: Game Statistics Accuracy
Validates: Requirements 12.2, 12.5
"""
import pytest
import time
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, engine


# Create client once
client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Reset database once before all tests"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Small delay to let threads settle
    time.sleep(0.1)


class TestGameSessionState:
    """
    Property 17: Game Session State
    For any game session, the state should accurately reflect
    all game actions performed.
    
    **Validates: Requirements 12.2**
    """
    
    def test_session_lifecycle(self):
        """
        Feature: ai-companion, Property 17: Game Session State
        
        Test complete session lifecycle: create, play, end.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "GameBot",
            "personality": "Playful"
        })
        assert companion_response.status_code == 200
        companion_id = companion_response.json()["id"]
        time.sleep(0.05)  # Small delay
        
        # Create trivia session
        session_response = client.post("/api/games/sessions", json={
            "game_id": "trivia",
            "companion_id": companion_id
        })
        assert session_response.status_code == 200
        session = session_response.json()
        session_id = session["id"]
        
        assert session["game_id"] == "trivia"
        assert session["is_active"] == True
        assert "state" in session
        time.sleep(0.05)
        
        # Answer a question
        state = session["state"]
        first_question = state["questions"][0]
        answer_response = client.post(f"/api/games/sessions/{session_id}/trivia", json={
            "answer": first_question["answer"]
        })
        assert answer_response.status_code == 200
        result = answer_response.json()
        assert result["correct"] == True
        assert result["state"]["user_score"] == 1
        time.sleep(0.05)
        
        # End session
        end_response = client.post(f"/api/games/sessions/{session_id}/end")
        assert end_response.status_code == 200
        record = end_response.json()
        assert record["winner"] in ["user", "companion", "tie"]
        time.sleep(0.05)
        
        # Verify inactive
        get_response = client.get(f"/api/games/sessions/{session_id}")
        assert get_response.json()["is_active"] == False


class TestGameStatisticsAccuracy:
    """
    Property 18: Game Statistics Accuracy
    For any set of completed games, the statistics should
    accurately reflect all game outcomes.
    
    **Validates: Requirements 12.5**
    """
    
    def test_stats_accuracy(self):
        """
        Feature: ai-companion, Property 18: Game Statistics Accuracy
        
        Statistics should accurately reflect game outcomes.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "StatsBot2",
            "personality": "Analytical"
        })
        assert companion_response.status_code == 200
        companion_id = companion_response.json()["id"]
        time.sleep(0.05)
        
        # Play 1 trivia game
        session_response = client.post("/api/games/sessions", json={
            "game_id": "trivia",
            "companion_id": companion_id
        })
        assert session_response.status_code == 200
        session_id = session_response.json()["id"]
        time.sleep(0.05)
        
        # Answer one question correctly
        state = session_response.json()["state"]
        client.post(f"/api/games/sessions/{session_id}/trivia", json={
            "answer": state["questions"][0]["answer"]
        })
        time.sleep(0.05)
        
        client.post(f"/api/games/sessions/{session_id}/end")
        time.sleep(0.05)
        
        # Get stats
        stats_response = client.get(f"/api/games/stats?companion_id={companion_id}")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # Verify counts
        assert stats["total_games"] == 1
        assert stats["wins"] + stats["losses"] + stats["ties"] == 1
        assert stats["total_user_score"] >= 1
        assert "trivia" in stats["games_by_type"]
        assert stats["games_by_type"]["trivia"]["played"] == 1
