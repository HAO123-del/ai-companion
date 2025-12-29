"""
Music models for the AI Companion application
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Float
from database import Base


class MusicTrack(Base):
    """Music track model"""
    __tablename__ = "music_tracks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    cover_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    duration = Column(Integer, default=0)  # Duration in seconds
    source = Column(String, default="local")  # 'local', 'url', 'search'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "cover_url": self.cover_url,
            "audio_url": self.audio_url,
            "duration": self.duration,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Playlist(Base):
    """Playlist model"""
    __tablename__ = "playlists"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    companion_id = Column(String, ForeignKey("companions.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "companion_id": self.companion_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PlaylistTrack(Base):
    """Association between playlist and tracks"""
    __tablename__ = "playlist_tracks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    playlist_id = Column(String, ForeignKey("playlists.id"), nullable=False)
    track_id = Column(String, ForeignKey("music_tracks.id"), nullable=False)
    position = Column(Integer, default=0)  # Order in playlist
    added_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "playlist_id": self.playlist_id,
            "track_id": self.track_id,
            "position": self.position,
            "added_at": self.added_at.isoformat() if self.added_at else None
        }


class PlaybackState(Base):
    """Current playback state for a companion"""
    __tablename__ = "playback_states"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    companion_id = Column(String, ForeignKey("companions.id"), nullable=False, unique=True)
    current_track_id = Column(String, ForeignKey("music_tracks.id"), nullable=True)
    playlist_id = Column(String, ForeignKey("playlists.id"), nullable=True)
    is_playing = Column(Boolean, default=False)
    progress = Column(Float, default=0.0)  # Progress in seconds
    volume = Column(Float, default=1.0)  # 0.0 to 1.0
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "companion_id": self.companion_id,
            "current_track_id": self.current_track_id,
            "playlist_id": self.playlist_id,
            "is_playing": self.is_playing,
            "progress": self.progress,
            "volume": self.volume,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
