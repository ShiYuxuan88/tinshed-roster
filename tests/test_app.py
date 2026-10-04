import sqlite3

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite3"), "SECRET_KEY": "test-key"})


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, url, data):
    client.get("/")
    with client.session_transaction() as session:
        token = session["csrf_token"]
    return client.post(url, data={**data, "csrf_token": token}, follow_redirects=True)


def setup_performance(client):
    post(client, "/volunteers", {"name": "Alex Morgan"})
    post(client, "/volunteers", {"name": "Taylor Lee"})
    post(client, "/productions", {"title": "The Cracked Pot"})
    post(client, "/performances", {
        "production_id": "1", "starts_at": "2026-10-09T19:30", "venue": "School of Arts Hall"
    })


def test_end_to_end_roster_and_persistence(client, app):
    setup_performance(client)
    response = post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})
    assert b"Assignment added" in response.data
    assert b"Alex Morgan" in response.data

    response = client.get("/my-roster?volunteer_id=1")
    assert b"The Cracked Pot" in response.data
    assert b"Stage manager" in response.data

    response = post(client, "/assignments/1/edit", {"role": "Lighting operator", "volunteer_id": "2"})
    assert b"Assignment updated" in response.data
    assert b"Taylor Lee" in response.data
    assert b"Stage manager" not in response.data.split(b"<tbody>", 1)[1].split(b"</tbody>", 1)[0]

    with sqlite3.connect(app.config["DATABASE"]) as connection:
        assert connection.execute("SELECT role, volunteer_id FROM assignments").fetchone() == ("Lighting operator", 2)

    response = post(client, "/assignments/1/delete", {})
    assert b"Assignment removed" in response.data
    assert b"No crew assigned yet" in response.data
    assert b"No assignments yet" in client.get("/my-roster?volunteer_id=2").data


def test_same_volunteer_or_role_cannot_be_assigned_twice(client):
    setup_performance(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})

    duplicate_person = post(client, "/performances/1", {"role": "Sound operator", "volunteer_id": "1"})
    duplicate_role = post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "2"})
    assert b"already assigned" in duplicate_person.data
    assert b"already assigned" in duplicate_role.data
    assert b"1 / 9 filled" in duplicate_role.data


def test_assignment_confirmation_toggle(client, app):
    setup_performance(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})

    with sqlite3.connect(app.config["DATABASE"]) as connection:
        assert connection.execute("SELECT confirmed FROM assignments").fetchone()[0] == 0

    confirmed = post(client, "/assignments/1/toggle-confirm", {})
    assert b"Assignment confirmed" in confirmed.data
    assert b"Confirmed" in confirmed.data

    with sqlite3.connect(app.config["DATABASE"]) as connection:
        assert connection.execute("SELECT confirmed FROM assignments").fetchone()[0] == 1

    pending = post(client, "/assignments/1/toggle-confirm", {})
    assert b"confirmation cleared" in pending.data

    with sqlite3.connect(app.config["DATABASE"]) as connection:
        assert connection.execute("SELECT confirmed FROM assignments").fetchone()[0] == 0


def test_deactivation_requires_unassigning_first(client):
    setup_performance(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})
    blocked = post(client, "/volunteers/1/toggle", {})
    assert b"Remove this volunteer&#39;s assignments" in blocked.data
    post(client, "/assignments/1/delete", {})
    allowed = post(client, "/volunteers/1/toggle", {})
    assert b"Inactive" in allowed.data


def test_post_requires_csrf_token(client):
    response = client.post("/volunteers", data={"name": "No token"})
    assert response.status_code == 400


def test_empty_states_and_health(client):
    assert b"No performances yet" in client.get("/").data
    assert b"No productions yet" in client.get("/productions").data
    assert client.get("/health").json == {"status": "ok"}


def test_production_mode_requires_secret(tmp_path):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({
            "DATABASE": str(tmp_path / "production.sqlite3"),
            "APP_ENV": "production",
            "SECRET_KEY": "local-development-only",
        })
