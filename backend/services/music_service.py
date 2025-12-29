"""
Music Service - Music playback and playlist management
Handles music search, playback state, and playlist operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.music import MusicTrack, Playlist, PlaylistTrack, PlaybackState


class MusicService:
    """
    Service for managing music playback and playlists.
    Provides search, playback control, and playlist management.
    """
    
    def search_tracks(
        self,
        db: Session,
        query: str,
        limit: int = 20
    ) -> List[MusicTrack]:
        """
        Search for music tracks by title or artist.
        
        Args:
            db: Database session
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching MusicTrack objects
        """
        # Return empty list for empty query
        if not query or not query.strip():
            return []
        
        search_pattern = f"%{query}%"
        
        tracks = (
            db.query(MusicTrack)
            .filter(
                or_(
                    MusicTrack.title.ilike(search_pattern),
                    MusicTrack.artist.ilike(search_pattern)
                )
            )
            .limit(limit)
            .all()
        )
        
        return tracks
    
    def get_track(self, db: Session, track_id: str) -> Optional[MusicTrack]:
        """Get a track by ID"""
        return db.query(MusicTrack).filter(MusicTrack.id == track_id).first()
    
    def create_track(
        self,
        db: Session,
        title: str,
        artist: str,
        audio_url: Optional[str] = None,
        cover_url: Optional[str] = None,
        duration: int = 0,
        source: str = "local"
    ) -> MusicTrack:
        """Create a new music track"""
        track = MusicTrack(
            title=title,
            artist=artist,
            audio_url=audio_url,
            cover_url=cover_url,
            duration=duration,
            source=source
        )
        db.add(track)
        db.commit()
        db.refresh(track)
        return track
    
    def get_playback_state(
        self,
        db: Session,
        companion_id: str
    ) -> Optional[PlaybackState]:
        """Get current playback state for a companion"""
        return (
            db.query(PlaybackState)
            .filter(PlaybackState.companion_id == companion_id)
            .first()
        )
    
    def get_or_create_playback_state(
        self,
        db: Session,
        companion_id: str
    ) -> PlaybackState:
        """Get or create playback state for a companion"""
        state = self.get_playback_state(db, companion_id)
        if not state:
            state = PlaybackState(companion_id=companion_id)
            db.add(state)
            db.commit()
            db.refresh(state)
        return state
    
    def play_track(
        self,
        db: Session,
        companion_id: str,
        track_id: str
    ) -> Dict[str, Any]:
        """
        Start playing a track.
        
        Args:
            db: Database session
            companion_id: ID of the companion
            track_id: ID of the track to play
            
        Returns:
            Updated playback state
        """
        track = self.get_track(db, track_id)
        if not track:
            return {"error": "Track not found"}
        
        state = self.get_or_create_playback_state(db, companion_id)
        state.current_track_id = track_id
        state.is_playing = True
        state.progress = 0.0
        
        db.commit()
        db.refresh(state)
        
        return {
            "state": state.to_dict(),
            "track": track.to_dict()
        }
    
    def pause_playback(
        self,
        db: Session,
        companion_id: str
    ) -> Dict[str, Any]:
        """Pause current playback"""
        state = self.get_playback_state(db, companion_id)
        if not state:
            return {"error": "No playback state found"}
        
        state.is_playing = False
        db.commit()
        db.refresh(state)
        
        return {"state": state.to_dict()}
    
    def resume_playback(
        self,
        db: Session,
        companion_id: str
    ) -> Dict[str, Any]:
        """Resume paused playback"""
        state = self.get_playback_state(db, companion_id)
        if not state:
            return {"error": "No playback state found"}
        
        if not state.current_track_id:
            return {"error": "No track to resume"}
        
        state.is_playing = True
        db.commit()
        db.refresh(state)
        
        return {"state": state.to_dict()}
    
    def update_progress(
        self,
        db: Session,
        companion_id: str,
        progress: float
    ) -> Dict[str, Any]:
        """Update playback progress"""
        state = self.get_playback_state(db, companion_id)
        if not state:
            return {"error": "No playback state found"}
        
        state.progress = progress
        db.commit()
        db.refresh(state)
        
        return {"state": state.to_dict()}
    
    def stop_playback(
        self,
        db: Session,
        companion_id: str
    ) -> Dict[str, Any]:
        """Stop playback and clear current track"""
        state = self.get_playback_state(db, companion_id)
        if not state:
            return {"error": "No playback state found"}
        
        state.current_track_id = None
        state.is_playing = False
        state.progress = 0.0
        
        db.commit()
        db.refresh(state)
        
        return {"state": state.to_dict()}

    
    # Playlist management
    def create_playlist(
        self,
        db: Session,
        companion_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Playlist:
        """Create a new playlist"""
        playlist = Playlist(
            companion_id=companion_id,
            name=name,
            description=description
        )
        db.add(playlist)
        db.commit()
        db.refresh(playlist)
        return playlist
    
    def get_playlist(self, db: Session, playlist_id: str) -> Optional[Playlist]:
        """Get a playlist by ID"""
        return db.query(Playlist).filter(Playlist.id == playlist_id).first()
    
    def list_playlists(
        self,
        db: Session,
        companion_id: str
    ) -> List[Playlist]:
        """List all playlists for a companion"""
        return (
            db.query(Playlist)
            .filter(Playlist.companion_id == companion_id)
            .all()
        )
    
    def delete_playlist(self, db: Session, playlist_id: str) -> bool:
        """Delete a playlist and its track associations"""
        playlist = self.get_playlist(db, playlist_id)
        if not playlist:
            return False
        
        # Delete track associations
        db.query(PlaylistTrack).filter(
            PlaylistTrack.playlist_id == playlist_id
        ).delete()
        
        db.delete(playlist)
        db.commit()
        return True
    
    def add_track_to_playlist(
        self,
        db: Session,
        playlist_id: str,
        track_id: str
    ) -> Optional[PlaylistTrack]:
        """Add a track to a playlist"""
        playlist = self.get_playlist(db, playlist_id)
        track = self.get_track(db, track_id)
        
        if not playlist or not track:
            return None
        
        # Get next position
        max_pos = (
            db.query(PlaylistTrack)
            .filter(PlaylistTrack.playlist_id == playlist_id)
            .count()
        )
        
        playlist_track = PlaylistTrack(
            playlist_id=playlist_id,
            track_id=track_id,
            position=max_pos
        )
        db.add(playlist_track)
        db.commit()
        db.refresh(playlist_track)
        return playlist_track
    
    def remove_track_from_playlist(
        self,
        db: Session,
        playlist_id: str,
        track_id: str
    ) -> bool:
        """Remove a track from a playlist"""
        result = (
            db.query(PlaylistTrack)
            .filter(
                PlaylistTrack.playlist_id == playlist_id,
                PlaylistTrack.track_id == track_id
            )
            .delete()
        )
        db.commit()
        return result > 0
    
    def get_playlist_tracks(
        self,
        db: Session,
        playlist_id: str
    ) -> List[Dict[str, Any]]:
        """Get all tracks in a playlist with their details"""
        playlist_tracks = (
            db.query(PlaylistTrack)
            .filter(PlaylistTrack.playlist_id == playlist_id)
            .order_by(PlaylistTrack.position)
            .all()
        )
        
        result = []
        for pt in playlist_tracks:
            track = self.get_track(db, pt.track_id)
            if track:
                result.append({
                    "playlist_track": pt.to_dict(),
                    "track": track.to_dict()
                })
        
        return result


# Global instance
music_service = MusicService()
