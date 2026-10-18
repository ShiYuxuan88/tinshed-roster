"""A3 regression checks using Flask's test client, not browser automation."""

import sqlite3

import pytest

from app import create_app
from test_app import app, client, post, setup_performance


def assignments(app):
    with sqlite3.connect(app.config["DATABASE"]) as connection:
        return connection.execute(
            "SELECT role, volunteer_id, confirmed FROM assignments ORDER BY id"
        ).fetchall()


@pytest.mark.parametrize("role,volunteer", [
    ("Lighting operator", "1"),
    ("Stage manager", "2"),
])
def test_changed_assignment_requires_new_confirmation(client, app, role, volunteer):
    setup_performance(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})
    post(client, "/assignments/1/toggle-confirm", {})
    assert assignments(app) == [("Stage manager", 1, 1)]

    response = post(client, "/assignments/1/edit", {"role": role, "volunteer_id": volunteer})

    assert b"Assignment updated" in response.data
    assert assignments(app) == [(role, int(volunteer), 0)]


def test_unchanged_assignment_keeps_confirmation(client, app):
    setup_performance(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})
    post(client, "/assignments/1/toggle-confirm", {})
    post(client, "/assignments/1/edit", {"role": "Stage manager", "volunteer_id": "1"})
    assert assignments(app) == [("Stage manager", 1, 1)]


def test_conflicting_edit_preserves_both_assignments(client, app):
    setup_performance(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})
    post(client, "/performances/1", {"role": "Sound operator", "volunteer_id": "2"})
    post(client, "/assignments/1/toggle-confirm", {})
    before = assignments(app)
    response = post(client, "/assignments/1/edit", {"role": "Sound operator", "volunteer_id": "1"})
    assert b"already assigned" in response.data
    assert assignments(app) == before


def test_removed_assignment_frees_original_role_for_another_volunteer(client, app):
    setup_performance(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})
    post(client, "/assignments/1/delete", {})
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "2"})
    post(client, "/performances/1", {"role": "Sound operator", "volunteer_id": "1"})
    assert assignments(app) == [("Stage manager", 2, 0), ("Sound operator", 1, 0)]


def test_confirmation_is_persisted_in_a_new_app_instance(client, app):
    setup_performance(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})
    post(client, "/assignments/1/toggle-confirm", {})
    restarted = create_app({
        "TESTING": True, "DATABASE": app.config["DATABASE"], "SECRET_KEY": "another-test-key"
    })
    response = restarted.test_client().get("/performances/1")
    assert response.status_code == 200
    assert b"Alex Morgan" in response.data
    assert b"Confirmed" in response.data
    assert assignments(restarted) == [("Stage manager", 1, 1)]


def test_confirmation_rejects_missing_csrf_without_mutating_data(client, app):
    setup_performance(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})
    response = client.post("/assignments/1/toggle-confirm")
    assert response.status_code == 400
    assert assignments(app) == [("Stage manager", 1, 0)]
