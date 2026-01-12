"""
Property-based tests for Reminder Scheduling
Property 11: Reminder Scheduling
Property 12: Inactivity Detection
Validates: Requirements 9.1, 9.5, 9.6
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, engine


# Test client
client = TestClient(app)


def setup_module(module):
    """Reset database once before all tests"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestReminderScheduling:
    """
    Property 11: Reminder Scheduling
    For any reminder with a scheduled time, the reminder should be stored 
    and retrievable, and the list should show all active reminders.
    
    **Validates: Requirements 9.1, 9.6**
    """
    
    def test_reminder_crud_round_trip(self):
        """
        Feature: ai-companion, Property 11: Reminder Scheduling
        
        For any valid reminder data, creating and retrieving should
        return the same data.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "ReminderTestBot",
            "personality": "Helpful"
        })
        companion_id = companion_response.json()["id"]
        
        # Test different reminder types
        test_cases = [
            ("scheduled", "Time to take a break!", True),
            ("greeting", "Good morning!", True),
            ("checkin", "How are you doing?", True),
        ]
        
        for reminder_type, message, enabled in test_cases:
            # Create reminder
            create_response = client.post("/api/reminders/", json={
                "companion_id": companion_id,
                "type": reminder_type,
                "message": message,
                "enabled": enabled
            })
            
            assert create_response.status_code == 200
            created = create_response.json()
            reminder_id = created["id"]
            
            # Retrieve and verify
            get_response = client.get(f"/api/reminders/{reminder_id}")
            assert get_response.status_code == 200
            retrieved = get_response.json()
            
            assert retrieved["companion_id"] == companion_id
            assert retrieved["type"] == reminder_type
            assert retrieved["message"] == message
            assert retrieved["enabled"] == enabled
    
    def test_reminder_list_returns_all_active(self):
        """
        Feature: ai-companion, Property 11: Reminder Scheduling
        
        Listing reminders should return all reminders for a companion,
        including both enabled and disabled ones.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "ListTestBot",
            "personality": "Helpful"
        })
        companion_id = companion_response.json()["id"]
        
        # Create multiple reminders
        for i in range(3):
            client.post("/api/reminders/", json={
                "companion_id": companion_id,
                "type": "scheduled",
                "message": f"Reminder {i}",
                "enabled": i % 2 == 0  # Alternate enabled/disabled
            })
        
        # List all reminders
        list_response = client.get(f"/api/reminders/?companion_id={companion_id}")
        reminders = list_response.json()
        
        assert len(reminders) == 3
        for r in reminders:
            assert r["companion_id"] == companion_id
    
    def test_reminder_toggle_enabled(self):
        """
        Feature: ai-companion, Property 11: Reminder Scheduling
        
        Toggling a reminder's enabled status should persist correctly.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "ToggleTestBot",
            "personality": "Helpful"
        })
        companion_id = companion_response.json()["id"]
        
        # Create a reminder (enabled by default)
        create_response = client.post("/api/reminders/", json={
            "companion_id": companion_id,
            "type": "scheduled",
            "message": "Test reminder",
            "enabled": True
        })
        reminder_id = create_response.json()["id"]
        
        # Toggle to disabled
        toggle_response = client.put(f"/api/reminders/{reminder_id}/toggle")
        assert toggle_response.status_code == 200
        assert toggle_response.json()["enabled"] == False
        
        # Toggle back to enabled
        toggle_response = client.put(f"/api/reminders/{reminder_id}/toggle")
        assert toggle_response.status_code == 200
        assert toggle_response.json()["enabled"] == True
    
    def test_greeting_creation(self):
        """
        Feature: ai-companion, Property 11: Reminder Scheduling
        
        Creating greeting reminders should work correctly.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "GreetingBot",
            "personality": "Friendly"
        })
        companion_id = companion_response.json()["id"]
        
        # Create morning greeting
        morning_response = client.post(
            f"/api/reminders/greeting?companion_id={companion_id}&greeting_type=morning"
        )
        assert morning_response.status_code == 200
        morning = morning_response.json()
        assert morning["type"] == "greeting"
        assert "早安" in morning["message"]
        
        # Create evening greeting
        evening_response = client.post(
            f"/api/reminders/greeting?companion_id={companion_id}&greeting_type=evening"
        )
        assert evening_response.status_code == 200
        evening = evening_response.json()
        assert evening["type"] == "greeting"
        assert "晚安" in evening["message"]


class TestInactivityDetection:
    """
    Property 12: Inactivity Detection
    For any configured inactivity period, if the user has not interacted 
    for that duration, a check-in notification should be triggered.
    
    **Validates: Requirements 9.5**
    """
    
    def test_inactivity_check_no_messages(self):
        """
        Feature: ai-companion, Property 12: Inactivity Detection
        
        When there are no messages, inactivity check should return
        appropriate status.
        """
        # Create a companion with no messages
        companion_response = client.post("/api/companions/", json={
            "name": "InactiveBot",
            "personality": "Helpful"
        })
        companion_id = companion_response.json()["id"]
        
        # Check inactivity
        response = client.get(
            f"/api/reminders/inactivity?companion_id={companion_id}&threshold_hours=24"
        )
        assert response.status_code == 200
        data = response.json()
        
        # No messages means not inactive (no baseline)
        assert data["is_inactive"] == False
        assert data["last_activity"] is None
    
    def test_inactivity_check_with_recent_message(self):
        """
        Feature: ai-companion, Property 12: Inactivity Detection
        
        When there is a recent message, user should not be marked inactive.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "ActiveBot",
            "personality": "Helpful"
        })
        companion_id = companion_response.json()["id"]
        
        # Create a recent message
        client.post("/api/messages/", json={
            "companion_id": companion_id,
            "role": "user",
            "content": "Hello!"
        })
        
        # Check inactivity with 24 hour threshold
        response = client.get(
            f"/api/reminders/inactivity?companion_id={companion_id}&threshold_hours=24"
        )
        assert response.status_code == 200
        data = response.json()
        
        # Recent message means not inactive
        assert data["is_inactive"] == False
        assert data["last_activity"] is not None
        assert data["hours_inactive"] < 24
    
    def test_checkin_reminder_creation(self):
        """
        Feature: ai-companion, Property 12: Inactivity Detection
        
        Creating a check-in reminder should work correctly.
        """
        # Create a companion
        companion_response = client.post("/api/companions/", json={
            "name": "CheckinBot",
            "personality": "Caring"
        })
        companion_id = companion_response.json()["id"]
        
        # Create check-in reminder
        response = client.post(
            f"/api/reminders/checkin?companion_id={companion_id}"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["type"] == "checkin"
        assert "想你" in data["message"] or "好久不见" in data["message"]
        assert data["enabled"] == True
