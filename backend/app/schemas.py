"""
schemas.py - The shapes of data going IN to and OUT of our API.

These are Pydantic models (not database tables). FastAPI uses them to:
  - reject bad input automatically (wrong email, short password)
  - control exactly what we send back (never the password hash!)
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------- Users and login ----------------

class UserCreate(BaseModel):
    """
    What a person sends to sign up.

    Example: {"email": "som@example.com", "full_name": "Som", "password": "som@1234"}
    """

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128, repr=False)


class UserOut(BaseModel):
    """
    What the API sends back about a user. Notice: NO password, NO hash.

    Example: {"id": 1, "email": "som@example.com", "full_name": "Som",
              "created_at": "2026-11-16T18:20:00Z"}
    """

    # Allow building this from a database User object (user.id, user.email, ...).
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    created_at: datetime


class Token(BaseModel):
    """
    What the API sends back after a successful login.

    Example: {"access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer"}
    """

    access_token: str
    token_type: str = "bearer"


# ---------------- Shows, seats and holds ----------------

class ShowOut(BaseModel):
    """
    One show in a list.

    Example: {"id": 1, "title": "The Last Monsoon", "category": "movie",
              "venue": "Forum Mall Screen 3, Bengaluru", "starts_at": "2026-12-05T13:30:00Z"}
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    venue: str
    starts_at: datetime


class SeatOut(BaseModel):
    """
    One seat on a seat map, with its live status.

    Example: {"id": 7, "label": "A7", "row_label": "A", "seat_number": 7,
              "price_paise": 15000, "status": "held"}
    """

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
    """
    The result of holding a seat.

    Example: {"show_id": 1, "seat_id": 7, "seat_label": "A7",
              "held_by_user_id": 31, "expires_in_seconds": 300}
    """

    show_id: int
    seat_id: int
    seat_label: str
    held_by_user_id: int
    expires_in_seconds: int