from datetime import datetime, timezone

from services.focus_sessions import calculate_elapsed_seconds


def test_focus_session_lifecycle_and_summary(client, user_factory):
    user = user_factory()
    started = client.post(
        "/focus-sessions/",
        headers=user["headers"],
        json={"title": "Study backend", "planned_duration_minutes": 25},
    )
    assert started.status_code == 201, started.text
    session = started.json()
    assert session["status"] == "running"
    assert session["planned_duration_seconds"] == 1500

    second_active = client.post(
        "/focus-sessions/",
        headers=user["headers"],
        json={"title": "Should not start yet"},
    )
    assert second_active.status_code == 409

    paused = client.post(
        f"/focus-sessions/{session['id']}/pause",
        headers=user["headers"],
    )
    assert paused.status_code == 200, paused.text
    assert paused.json()["status"] == "paused"

    invalid_pause = client.post(
        f"/focus-sessions/{session['id']}/pause",
        headers=user["headers"],
    )
    assert invalid_pause.status_code == 409

    resumed = client.post(
        f"/focus-sessions/{session['id']}/resume",
        headers=user["headers"],
    )
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["status"] == "running"

    completed = client.post(
        f"/focus-sessions/{session['id']}/complete",
        headers=user["headers"],
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    assert completed.json()["ended_at"] is not None
    assert completed.json()["elapsed_seconds"] >= 0

    invalid_complete = client.post(
        f"/focus-sessions/{session['id']}/complete",
        headers=user["headers"],
    )
    assert invalid_complete.status_code == 409

    today = datetime.now(timezone.utc).date().isoformat()
    summary = client.get(
        f"/focus-sessions/summary?start_date={today}&end_date={today}",
        headers=user["headers"],
    )
    assert summary.status_code == 200, summary.text
    assert summary.json()["completed_sessions"] == 1

    listing = client.get("/focus-sessions/?limit=10&offset=0", headers=user["headers"])
    assert listing.status_code == 200, listing.text
    assert listing.json()["has_more"] is False
    assert len(listing.json()["items"]) == 1


def test_focus_sessions_cannot_be_read_by_another_user(client, user_factory):
    owner = user_factory()
    other = user_factory()
    created = client.post(
        "/focus-sessions/",
        headers=owner["headers"],
        json={"title": "Private session"},
    )
    assert created.status_code == 201, created.text

    response = client.get(
        f"/focus-sessions/{created.json()['id']}",
        headers=other["headers"],
    )
    assert response.status_code == 404


def test_elapsed_time_excludes_pauses():
    start = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
    pause = datetime(2025, 1, 1, 10, 5, tzinfo=timezone.utc)
    session = {
        "started_at": start,
        "paused_at": pause,
        "ended_at": None,
        "paused_seconds": 0,
        "status": "paused",
    }
    assert calculate_elapsed_seconds(session, now=datetime(2025, 1, 1, 11, 0, tzinfo=timezone.utc)) == 300

    completed = {
        "started_at": start,
        "paused_at": None,
        "ended_at": datetime(2025, 1, 1, 10, 20, tzinfo=timezone.utc),
        "paused_seconds": 600,
        "status": "completed",
    }
    assert calculate_elapsed_seconds(completed) == 600
