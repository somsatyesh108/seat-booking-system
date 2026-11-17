"""
schemas.py - The shapes of data going IN to and OUT of our API (Pydantic models).
They reject bad input automatically and control what we send back (never password hashes).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------- Users and login ----------------

class UserCreate(BaseModel):
    """Signup input. Example: {"email": "som@example.com", "full_name": "Som", "password": "som@1234"}"""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128, repr=False)


class UserOut(BaseModel):
    """What we send back about a user. NO password, NO hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    created_at: datetime


class Token(BaseModel):
    """Login result. Example: {"access_token": "eyJ...", "token_type": "bearer"}"""

    access_token: str
    token_type: str = "bearer"


# ---------------- Shows, seats and holds ----------------

class ShowOut(BaseModel):
    """One showtime with its details. Example: {"title": "The Last Monsoon", "language": "Kannada", ...}"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    venue: str
    starts_at: datetime
    description: str = ""
    genre: str = ""
    language: str = ""
    duration_minutes: int | None = None
    age_rating: str = ""


class ShowListItem(ShowOut):
    """A showtime plus live numbers for listing pages: seats left and the cheapest price."""

    seats_total: int
    seats_booked: int
    min_price_paise: int | None = None


class SeatOut(BaseModel):
    """One seat on a seat map. Example: {"id": 7, "label": "A7", "status": "held", ...}"""

    id: int
    label: str
    row_label: str
    seat_number: int
    price_paise: int
    status: Literal["available", "held", "booked"]


class SeatMapOut(BaseModel):
    """A show plus all of its seats."""

    show: ShowOut
    seats: list[SeatOut]


class HoldOut(BaseModel):
    """Result of holding a seat. Example: {"seat_label": "A7", "expires_in_seconds": 300, ...}"""

    show_id: int
    seat_id: int
    seat_label: str
    held_by_user_id: int
    expires_in_seconds: int


# ---------------- Bookings ----------------

class BookingCreate(BaseModel):
    """Book the seats you hold (1 to 10, all-or-nothing). Example: {"show_id": 1, "seat_ids": [1, 2]}"""

    show_id: int
    seat_ids: list[int] = Field(min_length=1, max_length=10)

    @field_validator("seat_ids")
    @classmethod
    def no_duplicate_seats(cls, seat_ids: list[int]) -> list[int]:
        if len(set(seat_ids)) != len(seat_ids):
            raise ValueError("seat_ids must not contain the same seat twice")
        return seat_ids


class BookingOut(BaseModel):
    """One booked seat. Example: {"show_title": "The Last Monsoon", "seat_label": "A1", ...}"""

    id: int
    show_id: int
    show_title: str
    seat_id: int
    seat_label: str
    amount_paise: int
    created_at: datetime


class BookingConfirmation(BaseModel):
    """Result of a successful booking: every seat booked, plus the total price."""

    show_id: int
    bookings: list[BookingOut]
    total_paise: int