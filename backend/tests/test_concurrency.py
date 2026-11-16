"""
test_concurrency.py - Many users hit the SAME seat at the SAME moment. Exactly one may win.

Unlike other tests, these use the REAL database (each request gets its own session, like
real users), so data is created for real and deleted afterwards. Redis uses test DB 15.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from types import SimpleNamespace
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

import app.routers.bookings as bookings_module
from app.database import SessionLocal
from app.main import app
from app.models import Booking, Seat, Show, User
from app.redis_client import get_redis
from app.security import create_access_token

RACERS = 20
NAMES = ["Som", "Nahul", "Priya", "Arjun"]


# ---------- Setup: a real show with 20 seats and 20 real users ----------

@pytest.fixture
def race(test_redis):
    tag = uuid4().hex[:8]  # unique name so runs never clash
    with SessionLocal() as db:
        show = Show(
            title=f"Race Test {tag}",
            category="event",
            venue="Race Hall, Bengaluru",
            starts_at=datetime(2026, 12, 31, 21, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        )
        show.seats = [Seat(row_label="R", seat_number=n, price_paise=10000) for n in range(1, RACERS + 1)]
        users = [
            User(email=f"racer{i}.{tag}@example.com", full_name=NAMES[i % 4], hashed_password="unused")
            for i in range(RACERS)
        ]
        db.add(show)
        db.add_all(users)
        db.commit()
        data = SimpleNamespace(
            show_id=show.id,
            seat_ids=[seat.id for seat in show.seats],
            user_ids=[user.id for user in users],
        )

    app.dependency_overrides[get_redis] = lambda: test_redis  # real DB, test Redis
    try:
        yield data
    finally:
        app.dependency_overrides.clear()
        with SessionLocal() as db:  # clean up everything this race created
            db.execute(delete(Booking).where(Booking.seat_id.in_(data.seat_ids)))
            db.execute(delete(Seat).where(Seat.show_id == data.show_id))
            db.execute(delete(Show).where(Show.id == data.show_id))
            db.execute(delete(User).where(User.id.in_(data.user_ids)))
            db.commit()


def headers_for(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def run_all_at_once(count: int, action) -> list:
    """Start `count` threads, line them up at a barrier, then release them together."""
    starting_line = threading.Barrier(count)

    def racer(index: int):
        client = TestClient(app)
        starting_line.wait()  # everyone waits here... then all go at the same instant
        return action(client, index)

    with ThreadPoolExecutor(max_workers=count) as pool:
        return list(pool.map(racer, range(count)))


def bookings_for(seat_ids: list[int]) -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(Booking).where(Booking.seat_id.in_(seat_ids)))


class _AnyUser:
    """Compares equal to every user id: used to switch OFF the Redis hold check (Layer 1)."""

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


class _EveryoneHolds(dict):
    def get(self, key, default=None):
        return _AnyUser()


# ---------- The races ----------

def test_race_1_twenty_users_hold_one_seat_only_one_wins(race):
    seat = race.seat_ids[0]

    def hold(client, i):
        url = f"/shows/{race.show_id}/seats/{seat}/hold"
        return client.post(url, headers=headers_for(race.user_ids[i])).status_code

    codes = run_all_at_once(RACERS, hold)

    assert codes.count(201) == 1
    assert codes.count(409) == RACERS - 1


def test_race_2_twenty_users_book_one_seat_with_redis_check_off(race, monkeypatch):
    """Even with Layer 1 switched off, the row lock + UNIQUE allow exactly one booking."""
    monkeypatch.setattr(bookings_module, "get_holders", lambda *args: _EveryoneHolds())
    seat = race.seat_ids[0]

    def book(client, i):
        body = {"show_id": race.show_id, "seat_ids": [seat]}
        return client.post("/bookings", json=body, headers=headers_for(race.user_ids[i])).status_code

    codes = run_all_at_once(RACERS, book)

    assert codes.count(201) == 1
    assert codes.count(409) == RACERS - 1
    assert bookings_for([seat]) == 1


def test_race_3_real_flow_hold_then_book_same_seat(race):
    seat = race.seat_ids[0]

    def hold_then_book(client, i):
        headers = headers_for(race.user_ids[i])
        client.post(f"/shows/{race.show_id}/seats/{seat}/hold", headers=headers)
        body = {"show_id": race.show_id, "seat_ids": [seat]}
        return client.post("/bookings", json=body, headers=headers).status_code

    codes = run_all_at_once(RACERS, hold_then_book)

    assert codes.count(201) == 1
    assert bookings_for([seat]) == 1


def test_race_4_different_seats_all_succeed(race):
    """No false conflicts: 20 users booking 20 DIFFERENT seats at once all succeed."""

    def hold_then_book_own_seat(client, i):
        headers = headers_for(race.user_ids[i])
        seat = race.seat_ids[i]
        client.post(f"/shows/{race.show_id}/seats/{seat}/hold", headers=headers)
        body = {"show_id": race.show_id, "seat_ids": [seat]}
        return client.post("/bookings", json=body, headers=headers).status_code

    codes = run_all_at_once(RACERS, hold_then_book_own_seat)

    assert codes == [201] * RACERS
    assert bookings_for(race.seat_ids) == RACERS


def test_race_5_opposite_seat_order_no_deadlock(race, monkeypatch):
    """Half book [A, B], half book [B, A]. Locking in id order means no deadlock: one winner."""
    monkeypatch.setattr(bookings_module, "get_holders", lambda *args: _EveryoneHolds())
    first, second = race.seat_ids[0], race.seat_ids[1]

    def book_pair(client, i):
        seats = [first, second] if i % 2 == 0 else [second, first]
        body = {"show_id": race.show_id, "seat_ids": seats}
        return client.post("/bookings", json=body, headers=headers_for(race.user_ids[i])).status_code

    codes = run_all_at_once(RACERS, book_pair)

    assert codes.count(201) == 1
    assert codes.count(409) == RACERS - 1
    assert bookings_for([first, second]) == 2  # the winner got BOTH seats