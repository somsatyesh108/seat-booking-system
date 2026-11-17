"""
test_show_listing.py - The listing and detail endpoints return details and live seat numbers.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.models import Booking, Seat, Show, User

IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture
def movie(db_session):
    """A Kannada drama with 3 seats: A1 Rs 150, A2 Rs 250, A3 Rs 250. Priya has booked A2."""
    show = Show(
        title="Listing Test Movie",
        category="movie",
        venue="Test Screen, Bengaluru",
        starts_at=datetime(2026, 12, 31, 20, 0, tzinfo=IST),
        description="A test film.",
        genre="Drama",
        language="Kannada",
        duration_minutes=142,
        age_rating="UA",
    )
    show.seats = [
        Seat(row_label="A", seat_number=1, price_paise=15000),
        Seat(row_label="A", seat_number=2, price_paise=25000),
        Seat(row_label="A", seat_number=3, price_paise=25000),
    ]
    priya = User(email="priya.listing@example.com", full_name="Priya", hashed_password="unused")
    db_session.add_all([show, priya])
    db_session.flush()
    db_session.add(Booking(user_id=priya.id, seat_id=show.seats[1].id, amount_paise=25000))
    db_session.flush()
    return show


def test_list_shows_includes_details_and_live_seat_numbers(client, movie):
    item = next(i for i in client.get("/shows").json() if i["id"] == movie.id)

    assert item["language"] == "Kannada"
    assert item["genre"] == "Drama"
    assert item["duration_minutes"] == 142
    assert item["age_rating"] == "UA"
    assert item["seats_total"] == 3
    assert item["seats_booked"] == 1
    assert item["min_price_paise"] == 15000


def test_category_filter_returns_only_that_category(client, movie):
    movie_ids = [i["id"] for i in client.get("/shows?category=movie").json()]
    bus_ids = [i["id"] for i in client.get("/shows?category=bus").json()]

    assert movie.id in movie_ids
    assert movie.id not in bus_ids


def test_unknown_category_is_rejected(client):
    assert client.get("/shows?category=cricket").status_code == 422


def test_get_one_show(client, movie):
    response = client.get(f"/shows/{movie.id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Listing Test Movie"
    assert response.json()["seats_booked"] == 1


def test_get_unknown_show_is_404(client):
    assert client.get("/shows/999999").status_code == 404