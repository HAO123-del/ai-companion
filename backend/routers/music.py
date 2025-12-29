"""
Music API Router - Music playback and playlist management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from models.music import MusicTrack, Playlist, PlaylistTrack, PlaybackState
from services.music_service import music_service

router = APIRouter()


# Schemas
class TrackCreate(BaseModel):
    """Schema for creating a track"""
    title: str
    artist: str
    audio_url: Optional[str] = None
    cover_url: Optional[str] = None
    duration: int = 0
    source: str = "local"


class PlaylistCreate(BaseModel):
    """Schema for creating a playlist"""
    companion_id: str
    name: str
    description: Optional[str] = None


class PlaybackUpdate(BaseModel):
    """Schema for updating playback state"""
    progress: Optional[float] = None
    volume: Optional[float] = None


# Track endpoints
@router.post("/tracks")
async def create_track(data: TrackCreate, db: Session = Depends(get_db)):
    """Create a new music track"""
    track = music_service.create_track(
        db,
        title=data.title,
        artist=data.artist,
        audio_url=data.audio_url,
        cover_url=data.cover_url,
        duration=data.duration,
        source=data.source
    )
    return track.to_dict()


@router.get("/tracks")
async def list_tracks(
    limit: int = Query(50, description="Maximum number of tracks"),
    db: Session = Depends(get_db)
):
    """List all tracks"""
    tracks = db.query(MusicTrack).limit(limit).all()
    return [t.to_dict() for t in tracks]


@router.get("/tracks/search")
async def search_tracks(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """Search for tracks by title or artist"""
    tracks = music_service.search_tracks(db, q, limit)
    return [t.to_dict() for t in tracks]


@router.get("/tracks/{track_id}")
async def get_track(track_id: str, db: Session = Depends(get_db)):
    """Get a track by ID"""
    track = music_service.get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track.to_dict()


@router.delete("/tracks/{track_id}")
async def delete_track(track_id: str, db: Session = Depends(get_db)):
    """Delete a track"""
    track = music_service.get_track(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    db.delete(track)
    db.commit()
    return {"message": "Track deleted successfully"}


# Playback endpoints
@router.get("/playback/{companion_id}")
async def get_playback_state(companion_id: str, db: Session = Depends(get_db)):
    """Get current playback state for a companion"""
    state = music_service.get_or_create_playback_state(db, companion_id)
    result = state.to_dict()
    
    # Include current track details if playing
    if state.current_track_id:
        track = music_service.get_track(db, state.current_track_id)
        if track:
            result["current_track"] = track.to_dict()
    
    return result


@router.post("/playback/{companion_id}/play/{track_id}")
async def play_track(
    companion_id: str,
    track_id: str,
    db: Session = Depends(get_db)
):
    """Start playing a track"""
    result = music_service.play_track(db, companion_id, track_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/playback/{companion_id}/pause")
async def pause_playback(companion_id: str, db: Session = Depends(get_db)):
    """Pause current playback"""
    result = music_service.pause_playback(db, companion_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/playback/{companion_id}/resume")
async def resume_playback(companion_id: str, db: Session = Depends(get_db)):
    """Resume paused playback"""
    result = music_service.resume_playback(db, companion_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/playback/{companion_id}/stop")
async def stop_playback(companion_id: str, db: Session = Depends(get_db)):
    """Stop playback"""
    result = music_service.stop_playback(db, companion_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.put("/playback/{companion_id}/progress")
async def update_progress(
    companion_id: str,
    progress: float = Query(..., description="Progress in seconds"),
    db: Session = Depends(get_db)
):
    """Update playback progress"""
    result = music_service.update_progress(db, companion_id, progress)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# Playlist endpoints
@router.post("/playlists")
async def create_playlist(data: PlaylistCreate, db: Session = Depends(get_db)):
    """Create a new playlist"""
    playlist = music_service.create_playlist(
        db,
        companion_id=data.companion_id,
        name=data.name,
        description=data.description
    )
    return playlist.to_dict()


@router.get("/playlists")
async def list_playlists(
    companion_id: str = Query(..., description="Companion ID"),
    db: Session = Depends(get_db)
):
    """List all playlists for a companion"""
    playlists = music_service.list_playlists(db, companion_id)
    return [p.to_dict() for p in playlists]


@router.get("/playlists/{playlist_id}")
async def get_playlist(playlist_id: str, db: Session = Depends(get_db)):
    """Get a playlist by ID"""
    playlist = music_service.get_playlist(db, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist.to_dict()


@router.delete("/playlists/{playlist_id}")
async def delete_playlist(playlist_id: str, db: Session = Depends(get_db)):
    """Delete a playlist"""
    success = music_service.delete_playlist(db, playlist_id)
    if not success:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return {"message": "Playlist deleted successfully"}


@router.get("/playlists/{playlist_id}/tracks")
async def get_playlist_tracks(playlist_id: str, db: Session = Depends(get_db)):
    """Get all tracks in a playlist"""
    playlist = music_service.get_playlist(db, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    tracks = music_service.get_playlist_tracks(db, playlist_id)
    return tracks


@router.post("/playlists/{playlist_id}/tracks/{track_id}")
async def add_track_to_playlist(
    playlist_id: str,
    track_id: str,
    db: Session = Depends(get_db)
):
    """Add a track to a playlist"""
    result = music_service.add_track_to_playlist(db, playlist_id, track_id)
    if not result:
        raise HTTPException(status_code=404, detail="Playlist or track not found")
    return result.to_dict()


@router.delete("/playlists/{playlist_id}/tracks/{track_id}")
async def remove_track_from_playlist(
    playlist_id: str,
    track_id: str,
    db: Session = Depends(get_db)
):
    """Remove a track from a playlist"""
    success = music_service.remove_track_from_playlist(db, playlist_id, track_id)
    if not success:
        raise HTTPException(status_code=404, detail="Track not in playlist")
    return {"message": "Track removed from playlist"}
