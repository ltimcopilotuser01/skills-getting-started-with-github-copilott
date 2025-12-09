"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Join the school basketball team and compete in regional tournaments",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Swimming Club": {
            "description": "Improve your swimming technique and participate in swim meets",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["sarah@mergington.edu", "alex@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and develop acting skills",
            "schedule": "Wednesdays, 3:30 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["emily@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["lily@mergington.edu", "noah@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop critical thinking and public speaking skills through debates",
            "schedule": "Tuesdays, 4:00 PM - 5:30 PM",
            "max_participants": 16,
            "participants": ["william@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "Compete in science competitions and conduct experiments",
            "schedule": "Fridays, 3:30 PM - 5:30 PM",
            "max_participants": 24,
            "participants": ["ava@mergington.edu", "ethan@mergington.edu"]
        }
    }
    
    # Reset activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" in activities_data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant(self, client):
        """Test that duplicate signup returns an error"""
        # First signup
        client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
        
        # Second signup (duplicate)
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for a nonexistent activity"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_activity_at_capacity(self, client):
        """Test that signup fails when activity is at max capacity"""
        # Fill up Chess Club to capacity (max 12)
        current_participants = len(activities["Chess Club"]["participants"])
        spots_left = activities["Chess Club"]["max_participants"] - current_participants
        
        # Add participants to fill remaining spots
        for i in range(spots_left):
            response = client.post(
                f"/activities/Chess%20Club/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # Try to add one more (should fail)
        response = client.post(
            "/activities/Chess%20Club/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"].lower()


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # First signup
        client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
        
        # Then unregister
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "unregistered" in data["message"].lower()
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_not_signed_up(self, client):
        """Test that unregistering a non-participant returns an error"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister from a nonexistent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
