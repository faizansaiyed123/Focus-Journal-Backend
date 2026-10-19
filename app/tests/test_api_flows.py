from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from zoneinfo import ZoneInfo


def test_register_accepts_existing_frontend_name_field_and_login_alias(client):
    import uuid

    email = f"legacy-name-{uuid.uuid4().hex}@example.com"
    password = "StrongPass1!"
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "name": "Legacy Name Field",
            "password": password,
            "confirm_password": password,
        },
    )
    assert response.status_code == 201, response.text

    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    assert login.json()["access_token"]
    assert login.json()["token"] == login.json()["access_token"]

    me = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200, me.text
    assert me.json()["full_name"] == "Legacy Name Field"


def test_oauth_exchange_rejects_unknown_code(client):
    response = client.post("/auth/exchange", json={"code": "x" * 43})
    assert response.status_code == 401, response.text


def test_oauth_exchange_returns_access_token(client, user_factory, monkeypatch):
    from uuid import UUID

    user = user_factory()

    async def consume_code(_db, code):
        assert code == "c" * 43
        return UUID(user["user_id"])

    monkeypatch.setattr("api.routes.auth.consume_oauth_login_code", consume_code)
    response = client.post("/auth/exchange", json={"code": "c" * 43})
    assert response.status_code == 200, response.text
    assert response.json()["access_token"]
    assert "token" not in response.json()

    me = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer " + response.json()["access_token"]},
    )
    assert me.status_code == 200, me.text


def test_journal_crud_and_per_user_ownership(client, user_factory):
    owner = user_factory()
    other = user_factory()
    created = client.post(
        "/journal/",
        headers=owner["headers"],
        json={
            "title": "A useful workday",
            "content": "I completed the report without distractions.",
            "mood": "good",
            "focus_percent": 80,
            "tags": ["#Work", "focus", "work"],
            "is_favorite": False,
        },
    )
    assert created.status_code == 201, created.text
    entry = created.json()
    assert entry["tags"] == ["work", "focus"]

    fetched = client.get(f"/journal/{entry['id']}", headers=owner["headers"])
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["content"] == "I completed the report without distractions."

    forbidden = client.get(f"/journal/{entry['id']}", headers=other["headers"])
    assert forbidden.status_code == 404

    updated = client.put(
        f"/journal/{entry['id']}",
        headers=owner["headers"],
        json={"content": "Edited reflection", "tags": ["edited"]},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["content"] == "Edited reflection"
    assert updated.json()["tags"] == ["edited"]

    deleted = client.delete(f"/journal/{entry['id']}", headers=owner["headers"])
    assert deleted.status_code == 204
    assert client.get(f"/journal/{entry['id']}", headers=owner["headers"]).status_code == 404


def test_journal_period_comparison_uses_journal_entries_and_empty_ranges(client, user_factory):
    user = user_factory()
    created = client.post(
        "/journal/",
        headers=user["headers"],
        json={
            "title": "Comparison target",
            "content": "A focused session",
            "mood": "good",
            "focus_percent": 75,
            "tags": ["deep-work"],
        },
    )
    assert created.status_code == 201, created.text

    today = datetime.now(timezone.utc).date()
    body = {
        "start_range_1": (today - timedelta(days=6)).isoformat(),
        "end_range_1": today.isoformat(),
        "start_range_2": (today - timedelta(days=20)).isoformat(),
        "end_range_2": (today - timedelta(days=14)).isoformat(),
    }
    response = client.post("/journal/compare", headers=user["headers"], json=body)
    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["range_1"]["entry_count"] == 1
    assert payload["range_1"]["average_focus"] == 75
    assert payload["range_1"]["most_common_mood"] == "good"
    assert len(payload["range_1"]["days"]) == 1
    assert payload["range_2"]["entry_count"] == 0
    assert "average_focus" not in payload["range_2"]


def test_checkin_create_update_today_duplicate_and_streak(client, user_factory):
    user = user_factory()
    today = datetime.now(timezone.utc).date().isoformat()
    created = client.post(
        "/checkin/",
        headers=user["headers"],
        json={
            "date": today,
            "mood": "GOOD",
            "focus_percent": 45,
            "tags": ["#Study", "study"],
            "note": "Started with a clear priority.",
        },
    )
    assert created.status_code == 201, created.text
    checkin = created.json()
    assert checkin["mood"] == "good"
    assert checkin["tags"] == ["study"]

    duplicate = client.post(
        "/checkin/",
        headers=user["headers"],
        json={
            "date": today,
            "mood": "good",
            "focus_percent": 50,
            "tags": [],
        },
    )
    assert duplicate.status_code == 409

    assert client.get("/checkin/today", headers=user["headers"]).json()["checked"] is True
    assert (
        client.get("/checkin/checkin/today", headers=user["headers"]).json()["checked"]
        is True
    )

    updated = client.put(
        f"/checkin/{checkin['id']}",
        headers=user["headers"],
        json={"focus_percent": 92, "tags": ["updated"], "note": "Saved all fields"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["focus_percent"] == 92
    assert updated.json()["tags"] == ["updated"]
    assert updated.json()["note"] == "Saved all fields"

    streak = client.get("/checkin/streak", headers=user["headers"])
    assert streak.status_code == 200, streak.text
    assert streak.json()["current_streak"] == 1
    assert streak.json()["longest_streak"] == 1


def test_checkin_and_profile_dates_follow_user_timezone(client, user_factory):
    user = user_factory()
    updated = client.patch(
        "/profile/settings",
        headers=user["headers"],
        json={"timezone": "Asia/Kolkata"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["timezone"] == "Asia/Kolkata"

    today_local = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
    created = client.post(
        "/checkin/",
        headers=user["headers"],
        json={
            "date": today_local,
            "mood": "okay",
            "focus_percent": 20,
            "tags": [],
        },
    )
    assert created.status_code == 201, created.text
    assert client.get("/checkin/today", headers=user["headers"]).json()["checked"] is True


def test_search_binds_user_input_and_ai_requires_opt_in(client, user_factory):
    user = user_factory()
    response = client.post(
        "/journal/",
        headers=user["headers"],
        json={"title": "Keep data safe", "content": "A normal private note", "tags": ["private"]},
    )
    assert response.status_code == 201, response.text

    keyword = quote("' OR '1'='1")
    search = client.get(
        f"/checkin/journal/search?keyword={keyword}",
        headers=user["headers"],
    )
    assert search.status_code == 200, search.text
    assert isinstance(search.json()["data"], list)

    denied = client.get("/checkin/journal/insights", headers=user["headers"])
    assert denied.status_code == 403

    consent = client.patch(
        "/profile/settings",
        headers=user["headers"],
        json={"ai_processing_consent": True},
    )
    assert consent.status_code == 200, consent.text
    unavailable = client.get("/checkin/journal/insights", headers=user["headers"])
    assert unavailable.status_code == 503


def test_protected_resources_require_authentication(client):
    assert client.get("/journal/").status_code == 401
    assert client.get("/checkin/").status_code == 401
    assert client.get("/focus-sessions/").status_code == 401
