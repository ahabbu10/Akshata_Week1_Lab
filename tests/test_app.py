"""
Comprehensive tests for the FastAPI High School Management System
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestRootEndpoint:
    """Tests for the root endpoint GET /"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static index page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_success(self, client):
        """Test that activities endpoint returns 200 status"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that activities endpoint returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_activities_contains_all_activities(self, client):
        """Test that all 9 activities are returned"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball",
            "Tennis Club", "Art Studio", "Music Ensemble", "Debate Team", "Science Club"
        ]
        assert len(data) == 9
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for field in required_fields:
            assert field in activity

    def test_activity_participants_is_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert isinstance(activity["participants"], list)

    def test_activity_max_participants_is_int(self, client):
        """Test that max_participants is an integer"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert isinstance(activity["max_participants"], int)


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client, sample_email, sample_activity):
        """Test successful signup for an activity"""
        response = client.post(f"/activities/{sample_activity}/signup?email={sample_email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert sample_email in data["message"]
        assert sample_activity in data["message"]

    def test_signup_adds_participant_to_activity(self, client, sample_email, sample_activity):
        """Test that signup actually adds the participant to the activity"""
        # Get initial participant count
        response = client.get("/activities")
        initial_data = response.json()
        initial_count = len(initial_data[sample_activity]["participants"])
        
        # Sign up
        client.post(f"/activities/{sample_activity}/signup?email={sample_email}")
        
        # Check participant was added
        response = client.get("/activities")
        final_data = response.json()
        final_count = len(final_data[sample_activity]["participants"])
        
        assert final_count == initial_count + 1
        assert sample_email in final_data[sample_activity]["participants"]

    def test_signup_nonexistent_activity(self, client, sample_email, nonexistent_activity):
        """Test signup for non-existent activity returns 404"""
        response = client.post(f"/activities/{nonexistent_activity}/signup?email={sample_email}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_participant(self, client, sample_activity):
        """Test that signing up the same person twice returns 400"""
        # Get an existing participant
        response = client.get("/activities")
        data = response.json()
        existing_email = data[sample_activity]["participants"][0]
        
        # Try to sign up again
        response = client.post(f"/activities/{sample_activity}/signup?email={existing_email}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]


class TestRemoveParticipantEndpoint:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint"""

    def test_remove_participant_successful(self, client, sample_activity):
        """Test successful removal of a participant"""
        # Get an existing participant
        response = client.get("/activities")
        data = response.json()
        existing_email = data[sample_activity]["participants"][0]
        
        response = client.delete(f"/activities/{sample_activity}/participants?email={existing_email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert existing_email in data["message"]
        assert sample_activity in data["message"]

    def test_remove_participant_removes_from_activity(self, client, sample_activity):
        """Test that removal actually removes the participant from the activity"""
        # Get initial state
        response = client.get("/activities")
        initial_data = response.json()
        existing_email = initial_data[sample_activity]["participants"][0]
        initial_count = len(initial_data[sample_activity]["participants"])
        
        # Remove participant
        client.delete(f"/activities/{sample_activity}/participants?email={existing_email}")
        
        # Check participant was removed
        response = client.get("/activities")
        final_data = response.json()
        final_count = len(final_data[sample_activity]["participants"])
        
        assert final_count == initial_count - 1
        assert existing_email not in final_data[sample_activity]["participants"]

    def test_remove_participant_nonexistent_activity(self, client, sample_email, nonexistent_activity):
        """Test removal from non-existent activity returns 404"""
        response = client.delete(f"/activities/{nonexistent_activity}/participants?email={sample_email}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_remove_participant_not_enrolled(self, client, sample_activity, sample_email):
        """Test removal of participant not enrolled returns 404"""
        response = client.delete(f"/activities/{sample_activity}/participants?email={sample_email}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "Participant not found" in data["detail"]


class TestIntegrationScenarios:
    """Integration tests for complex workflows"""

    def test_signup_then_remove_workflow(self, client, sample_email, sample_activity):
        """Test signing up then removing a participant"""
        # Sign up
        client.post(f"/activities/{sample_activity}/signup?email={sample_email}")
        
        # Verify added
        response = client.get("/activities")
        data = response.json()
        assert sample_email in data[sample_activity]["participants"]
        
        # Remove
        client.delete(f"/activities/{sample_activity}/participants?email={sample_email}")
        
        # Verify removed
        response = client.get("/activities")
        data = response.json()
        assert sample_email not in data[sample_activity]["participants"]

    def test_multiple_signups(self, client, sample_activity):
        """Test multiple participants signing up for the same activity"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{sample_activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all are enrolled
        response = client.get("/activities")
        data = response.json()
        for email in emails:
            assert email in data[sample_activity]["participants"]