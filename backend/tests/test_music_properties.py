"""
Property-based tests for Music Player
Property 3: Music Player State Consistency
Property 4: Music Search Relevance
Validates: Requirements 4.3, 4.5
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, engine


# Test client
client = TestClient(app)


def setup_module(module):
    """Reset database once before all tests"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestMusicPlayerStateConsistency:
    """
    Property 3: Music Player State Consistency
    For any sequence of play/pause/skip operations on the music player,
    the playback state should accurately reflect the last operation performed.
    
    **Validates: Requirements 4.3**
    """
    
    def test_play_sets_playing_state(self):
        """
        Feature: ai-companion, Property 3: Music Player State Consistency
        
        When a track is played, the state should show is_playing=True.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "MusicBot",
            "personality": "Musical"
        })
        companion_id = companion_response.json()["id"]
        
        # Create a track
        track_response = client.post("/api/music/tracks", json={
            "title": "Test Song",
            "artist": "Test Artist",
            "duration": 180
        })
        track_id = track_response.json()["id"]
        
        # Play the track
        play_response = client.post(f"/api/music/playback/{companion_id}/play/{track_id}")
        assert play_response.status_code == 200
        
        state = play_response.json()["state"]
        assert state["is_playing"] == True
        assert state["current_track_id"] == track_id
        assert state["progress"] == 0.0
    
    def test_pause_sets_paused_state(self):
        """
        Feature: ai-companion, Property 3: Music Player State Consistency
        
        When playback is paused, the state should show is_playing=False.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "PauseBot",
            "personality": "Musical"
        })
        companion_id = companion_response.json()["id"]
        
        # Create and play a track
        track_response = client.post("/api/music/tracks", json={
            "title": "Pause Test Song",
            "artist": "Test Artist",
            "duration": 200
        })
        track_id = track_response.json()["id"]
        
        client.post(f"/api/music/playback/{companion_id}/play/{track_id}")
        
        # Pause
        pause_response = client.post(f"/api/music/playback/{companion_id}/pause")
        assert pause_response.status_code == 200
        
        state = pause_response.json()["state"]
        assert state["is_playing"] == False
        assert state["current_track_id"] == track_id  # Track still set
    
    def test_resume_restores_playing_state(self):
        """
        Feature: ai-companion, Property 3: Music Player State Consistency
        
        When playback is resumed, the state should show is_playing=True.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "ResumeBot",
            "personality": "Musical"
        })
        companion_id = companion_response.json()["id"]
        
        # Create, play, and pause a track
        track_response = client.post("/api/music/tracks", json={
            "title": "Resume Test Song",
            "artist": "Test Artist",
            "duration": 220
        })
        track_id = track_response.json()["id"]
        
        client.post(f"/api/music/playback/{companion_id}/play/{track_id}")
        client.post(f"/api/music/playback/{companion_id}/pause")
        
        # Resume
        resume_response = client.post(f"/api/music/playback/{companion_id}/resume")
        assert resume_response.status_code == 200
        
        state = resume_response.json()["state"]
        assert state["is_playing"] == True
        assert state["current_track_id"] == track_id
    
    def test_stop_clears_state(self):
        """
        Feature: ai-companion, Property 3: Music Player State Consistency
        
        When playback is stopped, the state should be cleared.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "StopBot",
            "personality": "Musical"
        })
        companion_id = companion_response.json()["id"]
        
        # Create and play a track
        track_response = client.post("/api/music/tracks", json={
            "title": "Stop Test Song",
            "artist": "Test Artist",
            "duration": 240
        })
        track_id = track_response.json()["id"]
        
        client.post(f"/api/music/playback/{companion_id}/play/{track_id}")
        
        # Stop
        stop_response = client.post(f"/api/music/playback/{companion_id}/stop")
        assert stop_response.status_code == 200
        
        state = stop_response.json()["state"]
        assert state["is_playing"] == False
        assert state["current_track_id"] is None
        assert state["progress"] == 0.0
    
    def test_play_pause_play_sequence(self):
        """
        Feature: ai-companion, Property 3: Music Player State Consistency
        
        A sequence of play -> pause -> play should result in playing state.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "SequenceBot",
            "personality": "Musical"
        })
        companion_id = companion_response.json()["id"]
        
        # Create a track
        track_response = client.post("/api/music/tracks", json={
            "title": "Sequence Test Song",
            "artist": "Test Artist",
            "duration": 260
        })
        track_id = track_response.json()["id"]
        
        # Play -> Pause -> Resume sequence
        client.post(f"/api/music/playback/{companion_id}/play/{track_id}")
        client.post(f"/api/music/playback/{companion_id}/pause")
        final_response = client.post(f"/api/music/playback/{companion_id}/resume")
        
        state = final_response.json()["state"]
        assert state["is_playing"] == True
        assert state["current_track_id"] == track_id


class TestMusicSearchRelevance:
    """
    Property 4: Music Search Relevance
    For any search query, all returned music tracks should contain
    the query term in either title or artist fields.
    
    **Validates: Requirements 4.5**
    """
    
    def test_search_by_title(self):
        """
        Feature: ai-companion, Property 4: Music Search Relevance
        
        Searching by title should return tracks with matching titles.
        """
        # Create tracks with specific titles
        client.post("/api/music/tracks", json={
            "title": "Beautiful Day",
            "artist": "U2",
            "duration": 240
        })
        client.post("/api/music/tracks", json={
            "title": "Beautiful Life",
            "artist": "Ace of Base",
            "duration": 210
        })
        client.post("/api/music/tracks", json={
            "title": "Ugly Truth",
            "artist": "Some Band",
            "duration": 180
        })
        
        # Search for "Beautiful"
        search_response = client.get("/api/music/tracks/search?q=Beautiful")
        assert search_response.status_code == 200
        
        results = search_response.json()
        assert len(results) >= 2
        
        # All results should contain "Beautiful" in title or artist
        for track in results:
            assert "beautiful" in track["title"].lower() or "beautiful" in track["artist"].lower()
    
    def test_search_by_artist(self):
        """
        Feature: ai-companion, Property 4: Music Search Relevance
        
        Searching by artist should return tracks with matching artists.
        """
        # Create tracks with specific artists
        client.post("/api/music/tracks", json={
            "title": "Song One",
            "artist": "Taylor Swift",
            "duration": 200
        })
        client.post("/api/music/tracks", json={
            "title": "Song Two",
            "artist": "Taylor Swift",
            "duration": 220
        })
        
        # Search for "Taylor"
        search_response = client.get("/api/music/tracks/search?q=Taylor")
        assert search_response.status_code == 200
        
        results = search_response.json()
        assert len(results) >= 2
        
        # All results should contain "Taylor" in title or artist
        for track in results:
            assert "taylor" in track["title"].lower() or "taylor" in track["artist"].lower()
    
    def test_search_case_insensitive(self):
        """
        Feature: ai-companion, Property 4: Music Search Relevance
        
        Search should be case-insensitive.
        """
        # Create a track
        client.post("/api/music/tracks", json={
            "title": "UPPERCASE SONG",
            "artist": "lowercase artist",
            "duration": 180
        })
        
        # Search with different cases
        search_upper = client.get("/api/music/tracks/search?q=UPPERCASE")
        search_lower = client.get("/api/music/tracks/search?q=uppercase")
        
        assert search_upper.status_code == 200
        assert search_lower.status_code == 200
        
        # Both should return results
        assert len(search_upper.json()) > 0
        assert len(search_lower.json()) > 0
    
    def test_search_empty_query_returns_empty(self):
        """
        Feature: ai-companion, Property 4: Music Search Relevance
        
        Empty search query should return empty results.
        """
        search_response = client.get("/api/music/tracks/search?q=")
        assert search_response.status_code == 200
        
        results = search_response.json()
        assert len(results) == 0
    
    def test_search_no_match_returns_empty(self):
        """
        Feature: ai-companion, Property 4: Music Search Relevance
        
        Search with no matching tracks should return empty results.
        """
        search_response = client.get("/api/music/tracks/search?q=xyznonexistent123")
        assert search_response.status_code == 200
        
        results = search_response.json()
        assert len(results) == 0
