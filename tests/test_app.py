"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that GET /activities returns known activities"""
        response = client.get("/activities")
        activities = response.json()
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Soccer Team" in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        activities = response.json()
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_returns_200_on_success(self):
        """Test that signup returns 200 on successful registration"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_returns_message(self):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        result = response.json()
        assert "message" in result
        assert "test@mergington.edu" in result["message"]
        assert "Chess Club" in result["message"]

    def test_signup_nonexistent_activity_returns_404(self):
        """Test that signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_participant_added_to_activity(self):
        """Test that a participant is actually added to the activity"""
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])

        # Sign up a new participant
        test_email = "new_participant@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={test_email}")

        # Get updated participant count
        response = client.get("/activities")
        updated_count = len(response.json()["Chess Club"]["participants"])
        participants = response.json()["Chess Club"]["participants"]

        assert updated_count == initial_count + 1
        assert test_email in participants

    def test_signup_full_activity_returns_400(self):
        """Test that signup to a full activity returns 400"""
        # Manually set an activity to be full for testing
        from src.app import activities

        activity_name = "Chess Club"
        max_participants = activities[activity_name]["max_participants"]
        activities[activity_name]["participants"] = [
            f"participant{i}@mergington.edu" for i in range(max_participants)
        ]

        response = client.post(
            f"/activities/{activity_name}/signup?email=full_test@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_returns_200_on_success(self):
        """Test that unregister returns 200 on successful removal"""
        # First sign up
        test_email = "unregister_test@mergington.edu"
        client.post(f"/activities/Soccer%20Team/signup?email={test_email}")

        # Then unregister
        response = client.post(
            f"/activities/Soccer%20Team/unregister?email={test_email}"
        )
        assert response.status_code == 200

    def test_unregister_returns_message(self):
        """Test that unregister returns a success message"""
        # First sign up
        test_email = "unregister_msg_test@mergington.edu"
        client.post(f"/activities/Track%20and%20Field/signup?email={test_email}")

        # Then unregister
        response = client.post(
            f"/activities/Track%20and%20Field/unregister?email={test_email}"
        )
        result = response.json()
        assert "message" in result
        assert test_email in result["message"]

    def test_unregister_nonexistent_activity_returns_404(self):
        """Test that unregister from non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_nonexistent_participant_returns_400(self):
        """Test that unregister non-existent participant returns 400"""
        response = client.post(
            "/activities/Art%20Club/unregister?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_participant_removed_from_activity(self):
        """Test that a participant is actually removed from the activity"""
        # First sign up
        test_email = "remove_test@mergington.edu"
        client.post(f"/activities/Drama%20Club/signup?email={test_email}")

        # Verify they were added
        response = client.get("/activities")
        participants_before = response.json()["Drama Club"]["participants"]
        assert test_email in participants_before

        # Unregister
        client.post(f"/activities/Drama%20Club/unregister?email={test_email}")

        # Verify they were removed
        response = client.get("/activities")
        participants_after = response.json()["Drama Club"]["participants"]
        assert test_email not in participants_after


class TestRoot:
    """Tests for GET / endpoint"""

    def test_root_redirect(self):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
