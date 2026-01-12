"""
Chat Service - MiniMax Chat API Integration
Handles AI conversation with personality-based responses
Using OpenAI-compatible API format
"""
import os
import httpx
from typing import AsyncGenerator, Optional, List, Dict, Any


class ChatService:
    """
    Service for handling chat interactions with MiniMax API.
    Uses OpenAI-compatible endpoint for simpler integration.
    """
    
    def __init__(self, api_key: str = None, group_id: str = None):
        # Use provided key or fall back to environment variable
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY", "")
        self.group_id = group_id or os.getenv("MINIMAX_GROUP_ID", "")
        self.base_url = "https://api.minimax.chat/v1"
        self.model = "abab6.5s-chat"
    
    def _build_system_prompt(
        self, 
        personality: str, 
        name: str,
        memory_context: str = ""
    ) -> str:
        """Build system prompt based on companion personality and memories"""
        base_prompt = f"""你是一个名叫{name}的AI陪伴智能体。

你的性格特点：
{personality}

请根据以上性格特点与用户进行自然、友好的对话。
- 保持对话的连贯性和上下文理解
- 用温暖、关心的语气回应
- 适当表达情感和个性
- 记住用户分享的信息并在适当时候引用"""
        
        if memory_context:
            base_prompt += f"\n\n{memory_context}"
        
        return base_prompt

    async def send_message(
        self,
        user_message: str,
        companion_name: str,
        personality: str,
        history: Optional[List[Dict[str, str]]] = None,
        memory_context: str = ""
    ) -> str:
        """Send a message and get a response from MiniMax API."""
        if not self.api_key:
            return f"你好！我是{companion_name}。很高兴和你聊天！（提示：请在设置中配置API Key）"
        
        personality = personality or "友好、温暖、善解人意"
        history = history or []
        
        # Build messages in OpenAI format
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(personality, companion_name, memory_context)
            }
        ]
        
        # Add history
        for msg in history[-10:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({
                "role": role,
                "content": msg.get("content", "")
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.8,
            "top_p": 0.95
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Use OpenAI-compatible endpoint
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                
                data = response.json()
                print(f"API Response: {data}")
                
                # Check for errors
                if "base_resp" in data:
                    status_code = data["base_resp"].get("status_code", 0)
                    if status_code != 0:
                        status_msg = data["base_resp"].get("status_msg", "未知错误")
                        return f"API错误: {status_msg}"
                
                # Parse response
                if "choices" in data and data["choices"]:
                    choice = data["choices"][0]
                    if "message" in choice:
                        return choice["message"].get("content", "抱歉，我无法回应。")
                    elif "text" in choice:
                        return choice["text"]
                
                return "抱歉，我现在无法回应。请稍后再试。"
                
        except httpx.TimeoutException:
            return "网络超时，请稍后重试。"
        except Exception as e:
            return f"发生错误：{str(e)}"

    async def stream_response(
        self,
        user_message: str,
        companion_name: str,
        personality: str,
        history: Optional[List[Dict[str, str]]] = None,
        memory_context: str = ""
    ) -> AsyncGenerator[str, None]:
        """Stream a response from MiniMax API."""
        if not self.api_key:
            yield f"你好！我是{companion_name}。很高兴和你聊天！"
            return
        
        # For now, use non-streaming
        response = await self.send_message(
            user_message, companion_name, personality, history, memory_context
        )
        yield response


# Global instance
chat_service = ChatService()
