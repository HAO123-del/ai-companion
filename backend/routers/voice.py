"""
Voice API Router - Voice cloning and TTS operations
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.companion import Companion
from services.voice_service import voice_service

router = APIRouter()


class TTSRequest(BaseModel):
    """Schema for TTS request"""
    text: str
    voice_id: str
    speed: Optional[float] = 1.0
    pitch: Optional[float] = 0


@router.post("/clone/{companion_id}")
async def clone_voice(
    companion_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None),
    x_group_id: Optional[str] = Header(None)
):
    """
    Clone a voice from uploaded audio and associate with companion.
    
    Requirements: 1.2, 7.1, 7.2
    """
    # Verify companion exists
    companion = db.query(Companion).filter(Companion.id == companion_id).first()
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")
    
    # Read audio data
    audio_data = await file.read()
    
    # Validate file size (minimum 10 seconds of audio, roughly 150KB for WAV)
    if len(audio_data) < 150000:
        raise HTTPException(
            status_code=400, 
            detail="Audio file too short. Please provide at least 10 seconds of clear speech."
        )
    
    # Generate voice ID
    voice_id = f"clone_{companion_id}_{uuid.uuid4().hex[:8]}"
    
    # Get API credentials from headers or environment
    import os
    api_key = x_api_key or os.getenv("MINIMAX_API_KEY", "")
    group_id = x_group_id or os.getenv("MINIMAX_GROUP_ID", "")
    
    if not api_key:
        raise HTTPException(status_code=400, detail="API key not configured. Please set it in Settings.")
    
    # Create voice service with credentials
    from services.voice_service import VoiceService
    voice_svc = VoiceService(api_key=api_key, group_id=group_id)
    
    # Clone voice
    result = await voice_svc.clone_voice(
        audio_data=audio_data,
        voice_id=voice_id,
        voice_name=f"{companion.name}_voice"
    )
    
    if result["success"]:
        # Update companion with new voice ID
        companion.voice_id = voice_id
        companion.voice_type = "cloned"
        db.commit()
        
        return {
            "success": True,
            "voice_id": voice_id,
            "message": "Voice cloned successfully"
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Voice cloning failed"))


@router.post("/tts")
async def text_to_speech(data: TTSRequest):
    """
    Convert text to speech using specified voice.
    
    Requirements: 7.3
    """
    result = await voice_service.synthesize_speech(
        text=data.text,
        voice_id=data.voice_id,
        speed=data.speed,
        pitch=data.pitch
    )
    
    if result["success"] and result["audio"]:
        return Response(
            content=result["audio"],
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "TTS failed"))


@router.get("/presets")
async def get_preset_voices():
    """
    Get list of available preset voices.
    
    Requirements: 1.3
    """
    return voice_service.get_preset_voices()


@router.put("/companion/{companion_id}/voice")
async def update_companion_voice(
    companion_id: str,
    voice_id: str,
    voice_type: str = "preset",
    db: Session = Depends(get_db)
):
    """
    Update companion's voice setting.
    
    Requirements: 7.5
    """
    companion = db.query(Companion).filter(Companion.id == companion_id).first()
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    
    companion.voice_id = voice_id
    companion.voice_type = voice_type
    db.commit()
    db.refresh(companion)
    
    return companion.to_dict()


@router.delete("/clone/{voice_id}")
async def delete_cloned_voice(voice_id: str):
    """
    Delete a cloned voice.
    """
    result = await voice_service.delete_cloned_voice(voice_id)
    
    if result["success"]:
        return {"message": "Voice deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Delete failed"))
