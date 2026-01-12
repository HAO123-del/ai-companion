"""
Property-based tests for Avatar Customization Persistence
Property 16: Avatar Customization Persistence
Validates: Requirements 11.5

Note: Using consolidated tests to avoid Windows SQLAlchemy threading issues.
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, engine


# Test client
client = TestClient(app)


# Test data for avatar customization
AVATAR_COLORS = [
    '#8B5CF6', '#6366F1', '#EC4899', '#F43F5E', 
    '#F97316', '#EAB308', '#22C55E', '#14B8A6'
]
AVATAR_STYLES = ['gradient', 'solid', 'outline']


def setup_module(module):
    """Reset database once before all tests"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestAvatarCustomizationPersistence:
    """
    Property 16: Avatar Customization Persistence
    For any avatar appearance customization, the changes should be 
    persisted and applied consistently across sessions.
    
    **Validates: Requirements 11.5**
    """
    
    def test_avatar_customization_round_trip_all_colors(self):
        """
        Feature: ai-companion, Property 16: Avatar Customization Persistence
        
        For any valid avatar customization (colors and style), saving to the 
        database and then retrieving should return the same customization values.
        Tests all color combinations.
        """
        for primary_color in AVATAR_COLORS:
            secondary_color = '#6366F1'
            avatar_style = 'gradient'
            
            # Create companion with avatar customization
            create_response = client.post("/api/companions/", json={
                "name": f"Test {primary_color}",
                "personality": "Friendly",
                "avatar_primary_color": primary_color,
                "avatar_secondary_color": secondary_color,
                "avatar_style": avatar_style
            })
            
            assert create_response.status_code == 200, f"Failed to create companion with color {primary_color}"
            created = create_response.json()
            companion_id = created["id"]
            
            # Retrieve and verify
            get_response = client.get(f"/api/companions/{companion_id}")
            assert get_response.status_code == 200
            retrieved = get_response.json()
            
            # Verify avatar customization is persisted
            assert retrieved["avatar_primary_color"] == primary_color
            assert retrieved["avatar_secondary_color"] == secondary_color
            assert retrieved["avatar_style"] == avatar_style
    
    def test_avatar_customization_round_trip_all_styles(self):
        """
        Feature: ai-companion, Property 16: Avatar Customization Persistence
        
        Tests all avatar style variations are persisted correctly.
        """
        for avatar_style in AVATAR_STYLES:
            primary_color = '#8B5CF6'
            secondary_color = '#6366F1'
            
            # Create companion with specific style
            create_response = client.post("/api/companions/", json={
                "name": f"Test {avatar_style}",
                "personality": "Friendly",
                "avatar_primary_color": primary_color,
                "avatar_secondary_color": secondary_color,
                "avatar_style": avatar_style
            })
            
            assert create_response.status_code == 200, f"Failed to create companion with style {avatar_style}"
            companion_id = create_response.json()["id"]
            
            # Verify style persisted
            get_response = client.get(f"/api/companions/{companion_id}")
            assert get_response.status_code == 200
            retrieved = get_response.json()
            
            assert retrieved["avatar_style"] == avatar_style
            assert retrieved["avatar_primary_color"] == primary_color
            assert retrieved["avatar_secondary_color"] == secondary_color
    
    def test_avatar_update_persistence(self):
        """
        Feature: ai-companion, Property 16: Avatar Customization Persistence
        
        For any avatar customization update, the changes should be persisted
        and retrievable after the update.
        """
        # Create companion with default avatar
        create_response = client.post("/api/companions/", json={
            "name": "Update Test Companion",
            "personality": "Friendly"
        })
        
        assert create_response.status_code == 200
        companion_id = create_response.json()["id"]
        
        # Test multiple updates
        update_cases = [
            ('#EC4899', '#F43F5E', 'solid'),
            ('#22C55E', '#14B8A6', 'outline'),
            ('#F97316', '#EAB308', 'gradient'),
        ]
        
        for primary, secondary, style in update_cases:
            # Update avatar customization
            update_response = client.put(f"/api/companions/{companion_id}", json={
                "avatar_primary_color": primary,
                "avatar_secondary_color": secondary,
                "avatar_style": style
            })
            
            assert update_response.status_code == 200
            
            # Retrieve and verify update persisted
            get_response = client.get(f"/api/companions/{companion_id}")
            assert get_response.status_code == 200
            retrieved = get_response.json()
            
            assert retrieved["avatar_primary_color"] == primary
            assert retrieved["avatar_secondary_color"] == secondary
            assert retrieved["avatar_style"] == style
    
    def test_avatar_color_combinations(self):
        """
        Test various color combinations are persisted correctly.
        """
        test_cases = [
            ('#8B5CF6', '#6366F1'),  # Purple combo
            ('#EC4899', '#F43F5E'),  # Pink/Red combo
            ('#22C55E', '#14B8A6'),  # Green/Teal combo
            ('#F97316', '#EAB308'),  # Orange/Yellow combo
        ]
        
        for primary, secondary in test_cases:
            create_response = client.post("/api/companions/", json={
                "name": f"Color Test {primary}",
                "personality": "Friendly",
                "avatar_primary_color": primary,
                "avatar_secondary_color": secondary
            })
            
            assert create_response.status_code == 200
            companion_id = create_response.json()["id"]
            
            get_response = client.get(f"/api/companions/{companion_id}")
            assert get_response.status_code == 200
            retrieved = get_response.json()
            
            assert retrieved["avatar_primary_color"] == primary
            assert retrieved["avatar_secondary_color"] == secondary
    
    def test_avatar_defaults(self):
        """
        Test that default avatar values are applied when not specified.
        """
        create_response = client.post("/api/companions/", json={
            "name": "Default Avatar Test",
            "personality": "Friendly"
        })
        
        assert create_response.status_code == 200
        companion_id = create_response.json()["id"]
        
        get_response = client.get(f"/api/companions/{companion_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        
        # Verify defaults are applied
        assert retrieved["avatar_primary_color"] == "#8B5CF6"
        assert retrieved["avatar_secondary_color"] == "#6366F1"
        assert retrieved["avatar_style"] == "gradient"
