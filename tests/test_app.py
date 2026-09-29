from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_configured_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activity_data = response.json()
    assert "Chess Club" in activity_data
    assert set(activity_data["Chess Club"]) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }


def test_signup_adds_participant(client):
    email = "new.student@mergington.edu"

    response = client.post(
        "/activities/Soccer Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Soccer Club"
    }
    assert email in activities["Soccer Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "new.student@mergington.edu"
    endpoint = "/activities/Soccer Club/signup"
    client.post(endpoint, params={"email": email})

    response = client.post(endpoint, params={"email": email})

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Student is already signed up for this activity"
    )
    assert activities["Soccer Club"]["participants"].count(email) == 1


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_removes_participant(client):
    email = "remove.student@mergington.edu"
    activities["Soccer Club"]["participants"].append(email)

    response = client.delete(
        "/activities/Soccer Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from Soccer Club"
    }
    assert email not in activities["Soccer Club"]["participants"]


def test_delete_returns_not_found_for_missing_participant(client):
    response = client.delete(
        "/activities/Soccer Club/signup",
        params={"email": "missing.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student is not signed up for this activity"
    )


def test_delete_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
