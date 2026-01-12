"""
Voice Service - MiniMax Voice Clone and TTS Integration
Handles voice cloning and text-to-speech synthesis
"""
import os
import httpx
import base64
from typing import Optional, List, Dict, Any


class VoiceService:
    """
    Service for handling voice cloning and TTS with MiniMax API.
    """
    
    def __init__(self, api_key: str = None, group_id: str = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY", "")
        self.group_id = group_id or os.getenv("MINIMAX_GROUP_ID", "")
        self.base_url = "https://api.minimax.chat/v1"
    
    async def clone_voice(
        self, 
        audio_data: bytes, 
        voice_id: str,
        voice_name: str = "custom_voice"
    ) -> Dict[str, Any]:
        """
        Clone a voice from audio sample using MiniMax API.
        
        Args:
            audio_data: Raw audio bytes (WAV/MP3 format)
            voice_id: Unique identifier for the cloned voice
            voice_name: Display name for the voice
            
        Returns:
            Dict with voice_id and status
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "API key not configured",
                "voice_id": None
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Step 1: Upload audio file to get file_id
                print(f"Uploading audio file for voice cloning... ({len(audio_data)} bytes)")
                upload_url = "https://api.minimax.chat/v1/files/upload"
                
                files = {
                    "file": ("voice_sample.wav", audio_data, "audio/wav")
                }
                data = {
                    "purpose": "voice_clone"
                }
                
                upload_response = await client.post(
                    upload_url,
                    headers=headers,
                    data=data,
                    files=files
                )
                
                print(f"Upload response status: {upload_response.status_code}")
                print(f"Upload response: {upload_response.text}")
                
                if upload_response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"File upload failed: {upload_response.status_code} - {upload_response.text}",
                        "voice_id": None
                    }
                
                upload_data = upload_response.json()
                
                # Check for errors in upload response
                if "base_resp" in upload_data and upload_data["base_resp"].get("status_code", 0) != 0:
                    return {
                        "success": False,
                        "error": f"File upload error: {upload_data['base_resp'].get('status_msg', 'Unknown')}",
                        "voice_id": None
                    }
                
                file_id = upload_data.get("file", {}).get("file_id")
                if not file_id:
                    return {
                        "success": False,
                        "error": "No file_id in upload response",
                        "voice_id": None
                    }
                
                print(f"File uploaded successfully, file_id: {file_id}")
                
                # Step 2: Clone the voice
                clone_url = "https://api.minimax.chat/v1/voice_clone"
                clone_payload = {
                    "file_id": file_id,
                    "voice_id": voice_id,
                    "text": "你好，这是一段测试语音，用于验证声音克隆效果。",
                    "model": "speech-01-turbo"
                }
                
                clone_headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                clone_response = await client.post(
                    clone_url,
                    headers=clone_headers,
                    json=clone_payload
                )
                
                print(f"Clone response status: {clone_response.status_code}")
                print(f"Clone response: {clone_response.text}")
                
                if clone_response.status_code == 200:
                    clone_data = clone_response.json()
                    
                    # Check for errors
                    if "base_resp" in clone_data and clone_data["base_resp"].get("status_code", 0) != 0:
                        return {
                            "success": False,
                            "error": f"Voice clone error: {clone_data['base_resp'].get('status_msg', 'Unknown')}",
                            "voice_id": None
                        }
                    
                    return {
                        "success": True,
                        "voice_id": voice_id,
                        "data": clone_data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Clone API error: {clone_response.status_code} - {clone_response.text}",
                        "voice_id": None
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timeout",
                "voice_id": None
            }
        except Exception as e:
            print(f"Voice clone exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "voice_id": None
            }

    async def synthesize_speech(
        self, 
        text: str, 
        voice_id: str,
        speed: float = 1.0,
        pitch: float = 0
    ) -> Dict[str, Any]:
        """
        Synthesize speech from text using MiniMax TTS API.
        
        Args:
            text: Text to synthesize
            voice_id: Voice ID (cloned or preset)
            speed: Speech speed (0.5-2.0)
            pitch: Pitch adjustment (-12 to 12)
            
        Returns:
            Dict with audio data or error
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "API key not configured",
                "audio": None
            }
        
        # Use preset voice if voice_id is invalid
        # MiniMax preset voice IDs
        preset_voices = [
            "Chinese_Gentle_Female", "Chinese_Sweet_Female", "Chinese_Lively_Female",
            "Chinese_Mature_Female", "Chinese_Warm_Male", "Chinese_Steady_Male",
            "Chinese_Young_Male", "English_expressive_narrator", "Cute_Anime_Female",
            "Narrator_Male", "male-qn-qingse", "female-shaonv", "female-yujie",
            "presenter_male", "presenter_female", "audiobook_male_1", "audiobook_male_2",
            "audiobook_female_1", "audiobook_female_2"
        ]
        
        # Use the voice_id as-is if it's a preset, otherwise use default
        # Cloned voices start with "clone_" but may not be valid
        actual_voice_id = voice_id if voice_id else "female-shaonv"
        
        # If it's a cloned voice that might not exist, try it first but be ready to fallback
        is_cloned_voice = voice_id and voice_id.startswith("clone_")
        if is_cloned_voice:
            # For cloned voices, we'll try it but fallback to preset if it fails
            print(f"Attempting to use cloned voice: '{actual_voice_id}'")
        else:
            # For preset voices, validate it exists
            if voice_id and voice_id not in preset_voices:
                actual_voice_id = "female-shaonv"
                print(f"Unknown voice_id '{voice_id}', using default: '{actual_voice_id}'")
            else:
                print(f"Using voice_id: '{actual_voice_id}'")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use MiniMax TTS API format for api.minimax.chat
        payload = {
            "model": "speech-01-turbo",
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": actual_voice_id,
                "speed": speed,
                "vol": 1,
                "pitch": int(pitch)
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try China mainland server first (api.minimax.chat)
                # as it may use the same API key as chat API
                tts_url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={self.group_id}"
                
                response = await client.post(
                    tts_url,
                    json=payload,
                    headers=headers
                )
                
                print(f"TTS API Response Status: {response.status_code}")
                print(f"TTS URL: {tts_url}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"TTS API Response: {data}")
                    
                    # Check for API errors
                    if "base_resp" in data:
                        status_code = data["base_resp"].get("status_code", 0)
                        if status_code != 0:
                            error_msg = data['base_resp'].get('status_msg', 'Unknown')
                            
                            # If cloned voice failed, retry with preset voice
                            if is_cloned_voice and ("voice" in error_msg.lower() or "not exist" in error_msg.lower()):
                                print(f"Cloned voice failed, retrying with preset voice...")
                                payload["voice_setting"]["voice_id"] = "female-shaonv"
                                retry_response = await client.post(tts_url, json=payload, headers=headers)
                                if retry_response.status_code == 200:
                                    data = retry_response.json()
                                    if "base_resp" in data and data["base_resp"].get("status_code", 0) != 0:
                                        return {
                                            "success": False,
                                            "error": f"TTS API error: {data['base_resp'].get('status_msg', 'Unknown')}",
                                            "audio": None
                                        }
                                else:
                                    return {
                                        "success": False,
                                        "error": f"TTS API error: {error_msg}",
                                        "audio": None
                                    }
                            else:
                                return {
                                    "success": False,
                                    "error": f"TTS API error: {error_msg}",
                                    "audio": None
                                }
                    
                    # Get audio from response - t2a_v2 returns hex format by default
                    if "data" in data and "audio" in data["data"]:
                        audio_hex = data["data"]["audio"]
                        # Decode hex string to bytes
                        audio_bytes = bytes.fromhex(audio_hex)
                        print(f"TTS Audio decoded: {len(audio_bytes)} bytes")
                        return {
                            "success": True,
                            "audio": audio_bytes,
                            "format": "mp3"
                        }
                    
                    # Handle URL format if returned
                    if "data" in data and "audio_url" in data["data"]:
                        audio_url = data["data"]["audio_url"]
                        # Download audio from URL
                        audio_response = await client.get(audio_url)
                        if audio_response.status_code == 200:
                            return {
                                "success": True,
                                "audio": audio_response.content,
                                "format": "mp3"
                            }
                    
                    # Fallback for old format (hex)
                    if "audio_file" in data:
                        audio_bytes = bytes.fromhex(data["audio_file"])
                        return {
                            "success": True,
                            "audio": audio_bytes,
                            "format": "mp3"
                        }
                    
                    return {
                        "success": False,
                        "error": f"No audio in response: {list(data.keys())}",
                        "audio": None
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code} - {response.text}",
                        "audio": None
                    }
                    
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Request timeout",
                "audio": None
            }
        except Exception as e:
            print(f"TTS Exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio": None
            }

    def get_preset_voices(self) -> List[Dict[str, str]]:
        """
        Get list of available preset voices.
        
        Returns:
            List of preset voice options
        """
        # MiniMax TTS v2 preset voices
        return [
            {"id": "Chinese_Gentle_Female", "name": "温柔女声", "gender": "female"},
            {"id": "Chinese_Sweet_Female", "name": "甜美女声", "gender": "female"},
            {"id": "Chinese_Lively_Female", "name": "活泼女声", "gender": "female"},
            {"id": "Chinese_Mature_Female", "name": "成熟女声", "gender": "female"},
            {"id": "Chinese_Warm_Male", "name": "温暖男声", "gender": "male"},
            {"id": "Chinese_Steady_Male", "name": "稳重男声", "gender": "male"},
            {"id": "Chinese_Young_Male", "name": "青年男声", "gender": "male"},
            {"id": "English_expressive_narrator", "name": "英文叙述者", "gender": "neutral"},
            {"id": "Cute_Anime_Female", "name": "可爱动漫女声", "gender": "female"},
            {"id": "Narrator_Male", "name": "男性旁白", "gender": "male"},
        ]

    async def delete_cloned_voice(self, voice_id: str) -> Dict[str, Any]:
        """
        Delete a cloned voice.
        
        Args:
            voice_id: ID of the voice to delete
            
        Returns:
            Dict with success status
        """
        if not self.api_key:
            return {"success": False, "error": "API key not configured"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{self.base_url}/voice_clone/{voice_id}?GroupId={self.group_id}",
                    headers=headers
                )
                
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance
voice_service = VoiceService()
