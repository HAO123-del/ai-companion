# -*- coding: utf-8 -*-
"""
Memory Service - Memory retrieval and management
Handles memory extraction, storage, and context injection for chat
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.memory import Memory


class MemoryService:
    """
    Service for managing companion memories.
    Provides memory retrieval, relevance scoring, and context building.
    """
    
    def __init__(self):
        self.max_memories_in_context = 5
    
    def get_relevant_memories(
        self,
        db: Session,
        companion_id: str,
        context: str,
        limit: int = 5
    ) -> List[Memory]:
        """Get memories relevant to a given context using keyword matching."""
        memories = (
            db.query(Memory)
            .filter(Memory.companion_id == companion_id)
            .all()
        )
        
        if not memories:
            return []
        
        context_words = set(context.lower().split())
        scored_memories = []
        
        for memory in memories:
            content_words = set(memory.content.lower().split())
            overlap = len(context_words & content_words)
            if overlap > 0:
                relevance_score = overlap * 0.5 + memory.importance * 0.5
                scored_memories.append((memory, relevance_score))
        
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        top_memories = [m for m, _ in scored_memories[:limit]]
        
        for memory in top_memories:
            memory.last_accessed_at = datetime.utcnow()
        db.commit()
        
        return top_memories
    
    def get_memories_by_importance(
        self,
        db: Session,
        companion_id: str,
        limit: int = 5
    ) -> List[Memory]:
        """Get top memories sorted by importance."""
        memories = (
            db.query(Memory)
            .filter(Memory.companion_id == companion_id)
            .order_by(Memory.importance.desc(), Memory.created_at.desc())
            .limit(limit)
            .all()
        )
        return memories
    
    def get_recent_memories(
        self,
        db: Session,
        companion_id: str,
        limit: int = 5
    ) -> List[Memory]:
        """Get recently accessed memories."""
        memories = (
            db.query(Memory)
            .filter(Memory.companion_id == companion_id)
            .order_by(
                Memory.last_accessed_at.desc().nullslast(),
                Memory.importance.desc()
            )
            .limit(limit)
            .all()
        )
        return memories
    
    def build_memory_context(self, memories: List[Memory]) -> str:
        """Build a context string from memories for injection into chat prompt."""
        if not memories:
            return ""
        
        memory_lines = []
        for memory in memories:
            category_label = {
                "preference": "偏好",
                "fact": "事实",
                "event": "事件"
            }.get(memory.category, memory.category)
            memory_lines.append(f"- [{category_label}] {memory.content}")
        
        return "关于用户的记忆：\n" + "\n".join(memory_lines)
    
    def extract_memories_from_conversation(
        self,
        messages: List[Dict[str, str]],
        companion_id: str
    ) -> List[Dict]:
        """Extract potential memories from a conversation."""
        potential_memories = []
        
        preference_keywords = ["喜欢", "爱", "讨厌", "不喜欢", "偏好", "最爱"]
        fact_keywords = ["我是", "我叫", "我的", "我在", "我住", "我工作"]
        event_keywords = ["今天", "昨天", "明天", "上周", "下周", "计划"]
        
        for msg in messages:
            if msg.get("role") != "user":
                continue
            
            content = msg.get("content", "")
            
            for keyword in preference_keywords:
                if keyword in content:
                    potential_memories.append({
                        "companion_id": companion_id,
                        "category": "preference",
                        "content": content,
                        "importance": 0.7
                    })
                    break
            
            for keyword in fact_keywords:
                if keyword in content:
                    potential_memories.append({
                        "companion_id": companion_id,
                        "category": "fact",
                        "content": content,
                        "importance": 0.8
                    })
                    break
            
            for keyword in event_keywords:
                if keyword in content:
                    potential_memories.append({
                        "companion_id": companion_id,
                        "category": "event",
                        "content": content,
                        "importance": 0.6
                    })
                    break
        
        return potential_memories


# Global instance
memory_service = MemoryService()
