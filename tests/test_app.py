from copy import deepcopy
import importlib

import pytest
from fastapi.testclient import TestClient

import src.app as app_module

client = TestClient(app_module.app)

# Preserve the initial activities state so tests are isolated
INITIAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Reset in-memory activities before each test
    app_module.activities = deepcopy(INITIAL_ACTIVITIES)
    yield


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Basketball Team" in data
    assert isinstance(data["Basketball Team"]["participants"], list)


def test_signup_success_and_duplicate():
    email = "teststudent@mergington.edu"
    activity = "Chess Club"

    # Signup should succeed
    resp = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Participant should now be present
    activities = client.get("/activities").json()
    assert email in activities[activity]["participants"]

    # Duplicate signup should return 400
    resp2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert resp2.status_code == 400


def test_signup_unknown_activity():
    resp = client.post("/activities/NonExistent/signup?email=a@b.com")
    assert resp.status_code == 404


def test_unregister_participant_success_and_errors():
    email = "alex@mergington.edu"  # exists in Theater Club
    activity = "Theater Club"

    # Ensure participant exists
    activities = client.get("/activities").json()
    assert email in activities[activity]["participants"]

    # Unregister should succeed
    resp = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # Now participant should be gone
    activities_after = client.get("/activities").json()
    assert email not in activities_after[activity]["participants"]

    # Unregistering again should return 404
    resp2 = client.delete(f"/activities/{activity}/participants?email={email}")
    assert resp2.status_code == 404

    # Unregister from non-existent activity
    resp3 = client.delete("/activities/NotFound/participants?email=a@b.com")
    assert resp3.status_code == 404
