"""Focused tests for the company's one-role-per-performance rule.

The company's operating rule is that a volunteer may hold at most one role in
any single performance, and an attempt to assign a second role to the same
volunteer in the same performance must be refused with a reason.

The existing suite covers this rule inside a test that also exercises the
"one volunteer per role" rule and asserts only on the shared message
"already assigned", so a failure of either rule alone cannot be attributed.
The tests below exercise each rule in isolation so that a future regression
turns exactly one named test red.
"""

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "assignment_rules.sqlite3"),
            "SECRET_KEY": "test-key",
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, url, data):
    """Submit a form with a valid CSRF token."""
    client.get("/")
    with client.session_transaction() as session:
        token = session["csrf_token"]
    return client.post(url, data={**data, "csrf_token": token}, follow_redirects=True)


def seed(client):
    """Create two volunteers, one production and two performances."""
    post(client, "/volunteers", {"name": "Alex Morgan"})
    post(client, "/volunteers", {"name": "Taylor Lee"})
    post(client, "/productions", {"title": "The Cracked Pot"})
    post(
        client,
        "/performances",
        {
            "production_id": "1",
            "starts_at": "2026-10-09T19:30",
            "venue": "School of Arts Hall",
        },
    )
    post(
        client,
        "/performances",
        {
            "production_id": "1",
            "starts_at": "2026-10-10T19:30",
            "venue": "School of Arts Hall",
        },
    )


def test_volunteer_cannot_hold_two_roles_in_one_performance(client):
    """The rule itself, with no other rule in play."""
    seed(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})

    refused = post(client, "/performances/1", {"role": "Sound operator", "volunteer_id": "1"})

    assert b"already assigned" in refused.data
    assert b"1 / 9 filled" in refused.data


def test_volunteer_can_hold_a_role_in_a_different_performance(client):
    """The boundary of the rule: it is per performance, not per volunteer."""
    seed(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})

    accepted = post(client, "/performances/2", {"role": "Sound operator", "volunteer_id": "1"})

    assert b"Assignment added" in accepted.data
    assert b"Alex Morgan" in accepted.data


def test_role_cannot_be_filled_twice_in_one_performance(client):
    """The second rule in isolation, so that the two can fail independently."""
    seed(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})

    refused = post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "2"})

    assert b"already assigned" in refused.data
    assert b"1 / 9 filled" in refused.data


def test_the_rule_releases_once_the_assignment_is_removed(client):
    """Removing an assignment must leave the position open and the volunteer free."""
    seed(client)
    post(client, "/performances/1", {"role": "Stage manager", "volunteer_id": "1"})
    refused = post(client, "/performances/1", {"role": "Sound operator", "volunteer_id": "1"})
    assert b"already assigned" in refused.data

    post(client, "/assignments/1/delete", {})

    accepted = post(client, "/performances/1", {"role": "Sound operator", "volunteer_id": "1"})
    assert b"Assignment added" in accepted.data
