"""
Call API Router - WebSocket voice call operations
"""
import json
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models.companion import Companion
from services.call_service import call_service, CallStatus

router = APIRouter()


class StartCallRequest(BaseModel):
    """Schema for starting a call"""
    companion_id: str


class EndCallRequest(BaseModel):
    """Schema for ending a call"""
    session_id: str


@router.post("/start")
async def start_call(data: StartCallRequest, db: Session = Depends(get_db)):
    """Start a new call session"""
    # Get companion
    companion = db.query(Companion).filter(Companion.id == data.companion_id).first()
    if not companion:
        raise HTTPException(status_code=404, detail="Companion not found")
    
    # Create session
    session = call_service.create_session(
        companion_id=companion.id,
        companion_name=companion.name,
        personality=companion.personality,
        voice_id=companion.voice_id or "Chinese_Gentle_Female"
    )
    
    return session.to_dict()


@router.post("/end")
async def end_call(data: EndCallRequest):
    """End a call session"""
    success = call_service.end_session(data.session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Call ended", "session_id": data.session_id}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get call session status"""
    session = call_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.websocket("/ws/{session_id}")
async def websocket_call(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time voice call.
    
    Protocol:
    - Client sends: {"type": "activate", "api_key": "...", "group_id": "..."} to start the call
    - Client sends: {"type": "speech", "text": "..."} for transcribed speech
    - Client sends: {"type": "end"} to end the call
    - Server sends: {"type": "status", "status": "..."} for status updates
    - Server sends: {"type": "response", "text": "...", "audio": "base64..."} for AI responses
    """
    await websocket.accept()
    
    session = call_service.get_session(session_id)
    if not session:
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close()
        return
    
    # Store API credentials for this session
    api_key = None
    group_id = None
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "status": session.status.value,
            "session": session.to_dict()
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "activate":
                # Get API credentials from activate message
                api_key = data.get("api_key")
                group_id = data.get("group_id")
                
                # Activate the call
                call_service.activate_session(session_id)
                await websocket.send_json({
                    "type": "status",
                    "status": CallStatus.ACTIVE.value,
                    "message": "Call activated"
                })
            
            elif msg_type == "speech":
                # Process user speech
                text = data.get("text", "")
                if text and session.status == CallStatus.ACTIVE:
                    # Get AI response with API key
                    result = await call_service.process_user_speech(
                        session_id, 
                        text,
                        api_key=api_key,
                        group_id=group_id
                    )
                    
                    response = {
                        "type": "response",
                        "text": result.get("text", ""),
                    }
                    
                    # Include audio if available
                    if result.get("audio"):
                        response["audio"] = base64.b64encode(result["audio"]).decode("utf-8")
                        response["audio_format"] = result.get("audio_format", "mp3")
                    
                    await websocket.send_json(response)
            
            elif msg_type == "ping":
                # Keep-alive ping
                await websocket.send_json({
                    "type": "pong",
                    "duration": session.get_duration()
                })
            
            elif msg_type == "end":
                # End the call
                call_service.end_session(session_id)
                await websocket.send_json({
                    "type": "status",
                    "status": CallStatus.ENDED.value,
                    "message": "Call ended"
                })
                break
    
    except WebSocketDisconnect:
        # Client disconnected
        call_service.end_session(session_id)
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        call_service.end_session(session_id)
    finally:
        try:
            await websocket.close()
        except:
            pass
