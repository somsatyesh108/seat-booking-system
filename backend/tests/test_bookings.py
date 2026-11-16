"""
test_bookings.py - Proves booking is safe: holds required, all-or-nothing, no double-booking.

Sandbox database (rolled back) + Redis database 15 (wiped): nothing real changes.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.holds import hold_key
from app.models import Seat, Show

IST = ZoneInfo("Asia/Kolkata")


# ---------- Test data and helpers ----------

@pytest.fixture
def show(db_session):
    """A test movie with seats A1 (Rs 150), A2 (Rs 250), A3 (Rs 250)."""
    new_show = Show(
        title="Booking Test Movie",
        category="movie",
        venue="Test Screen, Bengaluru",
        starts_at=datetime(2026, 12, 31, 20, 0, tzinfo=IST),
    )
    new_show.seats = [
        Seat(row_label="A", seat_number=1, price_paise=15000),
        Seat(row_label="A", seat_number=2, price_paise=25000),
        Seat(row_label="A", seat_number=3, price_paise=25000),
    ]
    db_session.add(new_show)
    db_session.flush()
    return new_show


def auth_headers(client, name: str) -> dict:
    """Sign up + log in Som / Nahul / Priya and return their auth header."""
    email = f"{name.lower()}@example.com"
    client.post("/auth/signup", json={"email": email, "full_name": name, "password": "secret@123"})
    token = client.post(
        "/auth/login", data={"username": email, "password": "secret@123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def user_id(client, headers: dict) -> int:
    return client.get("/auth/me", headers=headers).json()["id"]


def hold(client, show, seat, headers):
    return client.post(f"/shows/{show.id}/seats/{seat.id}/hold", headers=headers)


def book(client, show, seats, headers):
    return client.post(
        "/bookings", json={"show_id": show.id, "seat_ids": [s.id for s in seats]}, headers=headers
    )


def seat_status(client, show, label: str) -> str:
    seats = client.get(f"/shows/{show.id}/seats").json()["seats"]
    return next(seat["status"] for seat in seats if seat["label"] == label)


# ---------- Tests ----------

def test_som_books_the_seats_he_holds(client, show, test_redis):
    """Som holds A1 + A2 and books them -> 201, total Rs 400, seats booked, holds released."""
    a1, a2, _ = show.seats
    som = auth_headers(client, "Som")
    hold(client, show, a1, som)
    hold(client, show, a2, som)

    response = book(client, show, [a1, a2], som)

    assert response.status_code == 201
    body = response.json()
    assert body["total_paise"] == 40000
    assert sorted(b["seat_label"] for b in body["bookings"]) == ["A1", "A2"]
    assert seat_status(client, show, "A1") == "booked"
    assert seat_status(client, show, "A2") == "booked"
    assert test_redis.get(hold_key(show.id, a1.id)) is None  # hold released after booking


def test_cannot_book_a_seat_you_are_not_holding(client, show):
    """Som skips the hold step and tries to book A1 directly -> 409."""
    response = book(client, show, [show.seats[0]], auth_headers(client, "Som"))

    assert response.status_code == 409
    assert "Hold these seats" in response.json()["detail"]


def test_cannot_book_a_seat_someone_else_is_holding(client, show):
    """Som holds A1. Nahul tries to book A1 -> 409."""
    a1 = show.seats[0]
    hold(client, show, a1, auth_headers(client, "Som"))

    response = book(client, show, [a1], auth_headers(client, "Nahul"))

    assert response.status_code == 409
    assert "A1" in response.json()["detail"]


def test_booking_is_all_or_nothing(client, show, test_redis):
    """
    Priya already booked A2. Som holds A1 and (wrongly) appears to hold A2.
    Som books A1 + A2 -> 409, and A1 is NOT booked either (nothing half-done).
    """
    a1, a2, _ = show.seats
    priya = auth_headers(client, "Priya")
    hold(client, show, a2, priya)
    assert book(client, show, [a2], priya).status_code == 201

    som = auth_headers(client, "Som")
    hold(client, show, a1, som)
    test_redis.set(hold_key(show.id, a2.id), str(user_id(client, som)))  # stale/odd Redis state

    response = book(client, show, [a1, a2], som)

    assert response.status_code == 409
    assert "Already booked: A2" in response.json()["detail"]
    assert seat_status(client, show, "A1") == "held"  # still only held, NOT booked
    assert client.get("/bookings/me", headers=som).json() == []


def test_database_refuses_a_second_booking_even_if_redis_is_wrong(client, show, test_redis):
    """
    LAYER 2: Som books A1. Redis is then wrongly set to say Nahul holds A1.
    Nahul tries to book A1 -> the database check still refuses (409).
    """
    a1 = show.seats[0]
    som = auth_headers(client, "Som")
    hold(client, show, a1, som)
    assert book(client, show, [a1], som).status_code == 201

    nahul = auth_headers(client, "Nahul")
    test_redis.set(hold_key(show.id, a1.id), str(user_id(client, nahul)))

    response = book(client, show, [a1], nahul)

    assert response.status_code == 409
    assert "Already booked" in response.json()["detail"]


def test_same_seat_twice_in_one_request_is_rejected(client, show):
    a1 = show.seats[0]
    som = auth_headers(client, "Som")

    response = client.post(
        "/bookings", json={"show_id": show.id, "seat_ids": [a1.id, a1.id]}, headers=som
    )

    assert response.status_code == 422


def test_booking_a_seat_that_does_not_exist_is_404(client, show):
    response = client.post(
        "/bookings",
        json={"show_id": show.id, "seat_ids": [999999]},
        headers=auth_headers(client, "Som"),
    )

    assert response.status_code == 404


def test_booking_requires_login(client, show):
    response = client.post("/bookings", json={"show_id": show.id, "seat_ids": [show.seats[0].id]})

    assert response.status_code == 401


def test_my_bookings_shows_only_my_own(client, show):
    """Som books A1, Priya books A2. Som's list has only A1."""
    a1, a2, _ = show.seats
    som = auth_headers(client, "Som")
    priya = auth_headers(client, "Priya")
    hold(client, show, a1, som)
    book(client, show, [a1], som)
    hold(client, show, a2, priya)
    book(client, show, [a2], priya)

    response = client.get("/bookings/me", headers=som)

    assert response.status_code == 200
    assert [b["seat_label"] for b in response.json()] == ["A1"]
    assert response.json()[0]["show_title"] == "Booking Test Movie"