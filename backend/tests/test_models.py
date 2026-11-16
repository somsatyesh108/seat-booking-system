"""
test_models.py - Proves the DATABASE itself enforces our rules.

Each test tries to save something, and checks PostgreSQL accepts or rejects it.
All changes are undone after each test (see the db_session fixture in conftest.py).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Booking, Seat, Show, User

IST = ZoneInfo("Asia/Kolkata")


# ---------- Small helpers to create test data ----------

def make_user(db: Session, name: str) -> User:
    """Create a user like Som or Nahul (the password hash is fake; auth comes later)."""
    user = User(
        email=f"{name.lower()}@example.com",
        full_name=name,
        hashed_password="not-a-real-hash",
    )
    db.add(user)
    db.flush()  # send to PostgreSQL now, so the user gets an id
    return user


def make_show_with_one_seat(db: Session) -> tuple[Show, Seat]:
    """Create a test show with a single seat A1 costing Rs 250."""
    show = Show(
        title="Test Show",
        category="movie",
        venue="Test Venue, Bengaluru",
        starts_at=datetime(2026, 12, 31, 20, 0, tzinfo=IST),
    )
    seat = Seat(row_label="A", seat_number=1, price_paise=25000)
    show.seats = [seat]
    db.add(show)
    db.flush()
    return show, seat


# ---------- The tests ----------

def test_a_free_seat_can_be_booked(db_session):
    """Som books seat A1, which nobody has booked -> allowed."""
    som = make_user(db_session, "Som")
    _, seat = make_show_with_one_seat(db_session)

    booking = Booking(user_id=som.id, seat_id=seat.id, amount_paise=seat.price_paise)
    db_session.add(booking)
    db_session.flush()

    assert booking.id is not None
    assert seat.booking.user_id == som.id


def test_same_seat_cannot_be_booked_twice(db_session):
    """THE DOUBLE-BOOKING GUARD: Som books A1, then Nahul tries A1 -> rejected."""
    som = make_user(db_session, "Som")
    nahul = make_user(db_session, "Nahul")
    _, seat = make_show_with_one_seat(db_session)

    db_session.add(Booking(user_id=som.id, seat_id=seat.id, amount_paise=25000))
    db_session.flush()

    db_session.add(Booking(user_id=nahul.id, seat_id=seat.id, amount_paise=25000))
    with pytest.raises(IntegrityError) as error:
        db_session.flush()

    assert "uq_bookings_seat_id" in str(error.value)


def test_same_seat_label_cannot_exist_twice_in_one_show(db_session):
    """A show cannot have two seats both called A1."""
    show, _ = make_show_with_one_seat(db_session)

    db_session.add(Seat(show_id=show.id, row_label="A", seat_number=1, price_paise=25000))
    with pytest.raises(IntegrityError) as error:
        db_session.flush()

    assert "uq_seats_show_row_number" in str(error.value)


def test_invalid_show_category_is_rejected(db_session):
    """Only 'movie', 'bus' and 'event' are allowed; 'cricket' is rejected."""
    db_session.add(
        Show(
            title="Cricket Final",
            category="cricket",
            venue="Chinnaswamy Stadium, Bengaluru",
            starts_at=datetime(2026, 12, 20, 14, 0, tzinfo=IST),
        )
    )
    with pytest.raises(IntegrityError) as error:
        db_session.flush()

    assert "ck_shows_category_valid" in str(error.value)


def test_two_users_cannot_share_an_email(db_session):
    """Priya signs up twice with the same email -> second one rejected."""
    make_user(db_session, "Priya")

    with pytest.raises(IntegrityError) as error:
        make_user(db_session, "Priya")

    assert "ix_users_email" in str(error.value)


def test_negative_seat_price_is_rejected(db_session):
    """A seat cannot cost less than Rs 0."""
    show, _ = make_show_with_one_seat(db_session)

    db_session.add(Seat(show_id=show.id, row_label="B", seat_number=1, price_paise=-100))
    with pytest.raises(IntegrityError) as error:
        db_session.flush()

    assert "ck_seats_price_not_negative" in str(error.value)