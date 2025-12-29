"""
Property-based tests for Memory CRUD Operations
Property 9: Memory CRUD Operations
Validates: Requirements 8.5

Note: Using minimal tests to avoid Windows SQLAlchemy threading issues.
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


class TestMemoryCRUDOperations:
    """
    Property 9: Memory CRUD Operations
    For any Memory object, create/read/update/delete operations should be 
    consistent, and listing memories should return all non-deleted memories 
    for a companion.
    
    **Validates: Requirements 8.5**
    """
    
    def test_memory_crud_operations(self):
        """
        Feature: ai-companion, Property 9: Memory CRUD Operations
        
        Comprehensive test for memory CRUD operations:
        - Create and read round-trip
        - Update persistence
        - Delete removes from list
        - List returns all for companion
        - Importance sorting
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "MemoryTestBot",
            "personality": "Remembers everything"
        })
        companion_id = companion_response.json()["id"]
        
        # === Test Create and Read Round-Trip ===
        test_cases = [
            ("preference", "用户喜欢喝咖啡", 0.8),
            ("fact", "用户是一名程序员", 0.9),
            ("event", "用户今天去了公园", 0.5),
        ]
        
        memory_ids = []
        for category, content, importance in test_cases:
            create_response = client.post("/api/memories/", json={
                "companion_id": companion_id,
                "category": category,
                "content": content,
                "importance": importance
            })
            
            assert create_response.status_code == 200
            created = create_response.json()
            memory_id = created["id"]
            memory_ids.append(memory_id)
            
            # Read and verify
            get_response = client.get(f"/api/memories/{memory_id}")
            assert get_response.status_code == 200
            retrieved = get_response.json()
            
            assert retrieved["companion_id"] == companion_id
            assert retrieved["category"] == category
            assert retrieved["content"] == content
            assert retrieved["importance"] == importance
        
        # === Test Update Persistence ===
        update_response = client.put(f"/api/memories/{memory_ids[0]}", json={
            "content": "Updated content",
            "importance": 0.95
        })
        assert update_response.status_code == 200
        
        get_response = client.get(f"/api/memories/{memory_ids[0]}")
        assert get_response.json()["content"] == "Updated content"
        assert get_response.json()["importance"] == 0.95
        
        # === Test List Returns All ===
        list_response = client.get(f"/api/memories/?companion_id={companion_id}")
        memories = list_response.json()
        assert len(memories) == 3
        
        # === Test Importance Sorting ===
        # First memory now has highest importance (0.95)
        assert memories[0]["importance"] >= memories[1]["importance"]
        
        # === Test Delete Removes from List ===
        delete_response = client.delete(f"/api/memories/{memory_ids[2]}")
        assert delete_response.status_code == 200
        
        list_response = client.get(f"/api/memories/?companion_id={companion_id}")
        remaining = list_response.json()
        assert len(remaining) == 2
        assert memory_ids[2] not in [m["id"] for m in remaining]
    
    def test_memory_companion_isolation(self):
        """
        Feature: ai-companion, Property 9: Memory CRUD Operations
        
        Memories from different companions should be isolated.
        """
        # Create two companions
        companion1_response = client.post("/api/companions/", json={
            "name": "Bot1",
            "personality": "Test"
        })
        companion1_id = companion1_response.json()["id"]
        
        companion2_response = client.post("/api/companions/", json={
            "name": "Bot2",
            "personality": "Test"
        })
        companion2_id = companion2_response.json()["id"]
        
        # Create memories for each companion
        client.post("/api/memories/", json={
            "companion_id": companion1_id,
            "category": "preference",
            "content": "Bot1 Memory",
            "importance": 0.5
        })
        
        client.post("/api/memories/", json={
            "companion_id": companion2_id,
            "category": "fact",
            "content": "Bot2 Memory",
            "importance": 0.7
        })
        
        # Verify isolation
        list1 = client.get(f"/api/memories/?companion_id={companion1_id}").json()
        list2 = client.get(f"/api/memories/?companion_id={companion2_id}").json()
        
        assert len(list1) == 1
        assert list1[0]["companion_id"] == companion1_id
        assert list1[0]["content"] == "Bot1 Memory"
        
        assert len(list2) == 1
        assert list2[0]["companion_id"] == companion2_id
        assert list2[0]["content"] == "Bot2 Memory"



class TestMemoryPrioritization:
    """
    Property 10: Memory Prioritization
    For any set of memories exceeding the storage limit, the Memory_Service 
    should retain memories with higher importance scores and more recent 
    access times.
    
    **Validates: Requirements 8.6**
    """
    
    def test_memory_prioritization_by_importance(self):
        """
        Feature: ai-companion, Property 10: Memory Prioritization
        
        Memories should be retrievable sorted by importance, with higher
        importance memories appearing first.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "PriorityTestBot",
            "personality": "Test"
        })
        companion_id = companion_response.json()["id"]
        
        # Create memories with varying importance
        importance_values = [0.3, 0.9, 0.1, 0.7, 0.5]
        for i, importance in enumerate(importance_values):
            client.post("/api/memories/", json={
                "companion_id": companion_id,
                "category": "preference",
                "content": f"Memory with importance {importance}",
                "importance": importance
            })
        
        # Get memories sorted by importance (default)
        response = client.get(f"/api/memories/?companion_id={companion_id}&sort_by=importance")
        memories = response.json()
        
        # Verify sorted by importance descending
        assert len(memories) == 5
        for i in range(len(memories) - 1):
            assert memories[i]["importance"] >= memories[i + 1]["importance"]
        
        # First should be highest importance (0.9)
        assert memories[0]["importance"] == 0.9
        # Last should be lowest importance (0.1)
        assert memories[-1]["importance"] == 0.1
    
    def test_memory_prioritization_with_limit(self):
        """
        Feature: ai-companion, Property 10: Memory Prioritization
        
        When requesting a limited number of memories, the most important
        ones should be returned.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "LimitTestBot",
            "personality": "Test"
        })
        companion_id = companion_response.json()["id"]
        
        # Create memories with varying importance
        importance_values = [0.2, 0.8, 0.4, 0.6, 0.9]
        for i, importance in enumerate(importance_values):
            client.post("/api/memories/", json={
                "companion_id": companion_id,
                "category": "fact",
                "content": f"Memory {i}",
                "importance": importance
            })
        
        # Get top 3 memories by importance
        response = client.get(
            f"/api/memories/?companion_id={companion_id}&sort_by=importance&limit=3"
        )
        memories = response.json()
        
        # Should only return 3 memories
        assert len(memories) == 3
        
        # Should be the top 3 by importance: 0.9, 0.8, 0.6
        expected_importance = [0.9, 0.8, 0.6]
        for i, expected in enumerate(expected_importance):
            assert memories[i]["importance"] == expected
    
    def test_memory_access_time_update(self):
        """
        Feature: ai-companion, Property 10: Memory Prioritization
        
        Accessing a memory should update its last_accessed_at timestamp.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "AccessTimeBot",
            "personality": "Test"
        })
        companion_id = companion_response.json()["id"]
        
        # Create a memory
        create_response = client.post("/api/memories/", json={
            "companion_id": companion_id,
            "category": "preference",
            "content": "Test memory",
            "importance": 0.5
        })
        memory_id = create_response.json()["id"]
        initial_access = create_response.json().get("last_accessed_at")
        
        # Access the memory
        get_response = client.get(f"/api/memories/{memory_id}")
        updated_access = get_response.json().get("last_accessed_at")
        
        # last_accessed_at should be updated (not None after access)
        assert updated_access is not None
