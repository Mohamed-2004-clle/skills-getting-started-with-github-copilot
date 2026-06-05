from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original_activities))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["max_participants"] == 12


def test_signup_adds_student_to_activity_once():
    email = "new.student@mergington.edu"
    initial_count = len(activities["Chess Club"]["participants"])

    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert len(activities["Chess Club"]["participants"]) == initial_count + 1
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_signup_rejects_duplicate_registration():
    email = "repeat.student@mergington.edu"

    first_response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )
    second_response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already registered"


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Robotics%20Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"