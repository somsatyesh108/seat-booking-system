"""
test_holds.py - Tests for shows, seat maps and Redis seat holds through the API.

Uses the sandbox database (rolled back) and Redis database 15 (wiped), so nothing real changes.
"""

import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import select

import app.routers.shows as shows_module
from app.holds import hold_key
from app.models import Booking, Seat, Show, User

IST = ZoneInfo("Asia/Kolkata")


# ---------- Test data and helpers ----------

@pytest.fixture
def show(db_session):
    """A test movie with two seats, A1 and A2 (Rs 250 each)."""
    new_show = Show(
        title="Test Movie",
        category="movie",
        venue="Test Screen, Bengaluru",
        starts_at=datetime(2026, 12, 31, 20, 0, tzinfo=IST),
    )
    new_show.seats = [Seat(row_label="A", seat_number=n, price_paise=25000) for n in (1, 2)]
    db_session.add(new_show)
    db_session.flush()
    return new_show


def auth_headers(client, name: str) -> dict:
    """Sign up + log in a test user (Som, Nahul, Priya) and return their auth header."""
    email = f"{name.lower()}@example.com"
    client.post(
        "/auth/signup", json={"email": email, "full_name": name, "password": "secret@123"}
    )
    token = client.post(
        "/auth/login", data={"username": email, "password": "secret@123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def hold_url(show: Show, seat: Seat) -> str:
    return f"/shows/{show.id}/seats/{seat.id}/hold"


def seat_status(client, show: Show, label: str) -> str:
    """Read one seat's status ("available" / "held" / "booked") from the seat map."""
    seats = client.get(f"/shows/{show.id}/seats").json()["seats"]
    return next(seat["status"] for seat in seats if seat["label"] == label)


# ---------- Shows and seat map ----------

def test_list_shows_includes_the_new_show(client, show):
    response = client.get("/shows")

    assert response.status_code == 200
    assert "Test Movie" in [item["title"] for item in response.json()]


def test_seat_map_starts_with_every_seat_available(client, show):
    response = client.get(f"/shows/{show.id}/seats")

    assert response.status_code == 200
    seats = response.json()["seats"]
    assert [seat["label"] for seat in seats] == ["A1", "A2"]
    assert all(seat["status"] == "available" for seat in seats)


def test_seat_map_for_unknown_show_is_404(client):
    assert client.get("/shows/999999/seats").status_code == 404


# ---------- Holding seats ----------

def test_som_can_hold_a_free_seat(client, show):
    """Som holds A1 -> 201, about 300 seconds left, seat map shows it as held."""
    seat_a1 = show.seats[0]

    response = client.post(hold_url(show, seat_a1), headers=auth_headers(client, "Som"))

    assert response.status_code == 201
    body = response.json()
    assert body["seat_label"] == "A1"
    assert 290 <= body["expires_in_seconds"] <= 300
    assert seat_status(client, show, "A1") == "held"
    assert seat_status(client, show, "A2") == "available"


def test_nahul_cannot_hold_a_seat_som_is_holding(client, show):
    """THE HOLD GUARD: Som holds A1, then Nahul tries A1 -> 409."""
    seat_a1 = show.seats[0]
    client.post(hold_url(show, seat_a1), headers=auth_headers(client, "Som"))

    response = client.post(hold_url(show, seat_a1), headers=auth_headers(client, "Nahul"))

    assert response.status_code == 409
    assert "held by someone else" in response.json()["detail"]


def test_holding_your_own_seat_again_is_fine(client, show):
    """Som clicks 'hold' twice on A1 -> both succeed, he still holds it."""
    seat_a1 = show.seats[0]
    som = auth_headers(client, "Som")

    first = client.post(hold_url(show, seat_a1), headers=som)
    second = client.post(hold_url(show, seat_a1), headers=som)

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["held_by_user_id"] == first.json()["held_by_user_id"]


def test_holding_requires_login(client, show):
    response = client.post(hold_url(show, show.seats[0]))

    assert response.status_code == 401


def test_holding_a_seat_that_does_not_exist_is_404(client, show):
    response = client.post(
        f"/shows/{show.id}/seats/999999/hold", headers=auth_headers(client, "Som")
    )

    assert response.status_code == 404


def test_cannot_hold_a_seat_that_is_already_booked(client, show, db_session):
    """Priya already booked A2 -> nobody can hold it, and the seat map says booked."""
    seat_a2 = show.seats[1]
    priya_headers = auth_headers(client, "Priya")
    priya = db_session.scalar(select(User).where(User.email == "priya@example.com"))
    db_session.add(Booking(user_id=priya.id, seat_id=seat_a2.id, amount_paise=25000))
    db_session.flush()

    response = client.post(hold_url(show, seat_a2), headers=priya_headers)

    assert response.status_code == 409
    assert "already booked" in response.json()["detail"]
    assert seat_status(client, show, "A2") == "booked"


# ---------- Releasing and expiry ----------

def test_only_the_holder_can_release_a_hold(client, show):
    """Som holds A1. Nahul's release -> 404. Som's release -> 204, seat free again."""
    seat_a1 = show.seats[0]
    som = auth_headers(client, "Som")
    nahul = auth_headers(client, "Nahul")
    client.post(hold_url(show, seat_a1), headers=som)

    assert client.delete(hold_url(show, seat_a1), headers=nahul).status_code == 404
    assert client.delete(hold_url(show, seat_a1), headers=som).status_code == 204
    assert seat_status(client, show, "A1") == "available"


def test_hold_expires_and_the_seat_becomes_free(client, show, test_redis):
    """Som holds A1 but never pays. When the hold expires, Nahul can take it."""
    seat_a1 = show.seats[0]
    client.post(hold_url(show, seat_a1), headers=auth_headers(client, "Som"))

    # Speed up time: make Som's 5-minute hold expire in 100 milliseconds.
    test_redis.pexpire(hold_key(show.id, seat_a1.id), 100)
    time.sleep(0.3)

    assert seat_status(client, show, "A1") == "available"
    response = client.post(hold_url(show, seat_a1), headers=auth_headers(client, "Nahul"))
    assert response.status_code == 201


def test_redis_down_gives_a_clear_503(client, show, monkeypatch):
    """If Redis is unreachable, holding a seat returns 503 instead of crashing."""

    def redis_is_down(*args, **kwargs):
        raise RedisConnectionError("Redis is down")

    monkeypatch.setattr(shows_module, "try_hold_seat", redis_is_down)

    response = client.post(hold_url(show, show.seats[0]), headers=auth_headers(client, "Som"))

    assert response.status_code == 503