"""
seed.py - Fills the database with sample shows and seats for development.

Run from the backend folder with:  python -m app.seed
Safe to run more than once: it skips shows that already exist.
"""

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import Seat, Show

IST = ZoneInfo("Asia/Kolkata")

# Each sample show: details + how to build its seat grid.
SAMPLE_SHOWS = [
    {
        "title": "The Last Monsoon",
        "category": "movie",
        "venue": "Forum Mall Screen 3, Bengaluru",
        "starts_at": datetime(2026, 12, 5, 19, 0, tzinfo=IST),
        "rows": ["A", "B", "C", "D", "E"],
        "seats_per_row": 10,
        # Front rows A-B are cheaper (Rs 150), the rest Rs 250.
        "price_for_row": lambda row: 15000 if row in ("A", "B") else 25000,
    },
    {
        "title": "Bengaluru to Chennai Night Express",
        "category": "bus",
        "venue": "Majestic Bus Stand, Bengaluru",
        "starts_at": datetime(2026, 12, 6, 22, 30, tzinfo=IST),
        "rows": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
        "seats_per_row": 4,
        "price_for_row": lambda row: 80000,  # Rs 800 for every seat
    },
    {
        "title": "Indie Music Night",
        "category": "event",
        "venue": "Palace Grounds, Bengaluru",
        "starts_at": datetime(2026, 12, 12, 18, 0, tzinfo=IST),
        "rows": ["A", "B", "C"],
        "seats_per_row": 8,
        "price_for_row": lambda row: 99900,  # Rs 999 for every seat
    },
]


def build_seats(rows: list[str], seats_per_row: int, price_for_row) -> list[Seat]:
    """Create Seat objects like A1, A2, ... for every row."""
    return [
        Seat(row_label=row, seat_number=number, price_paise=price_for_row(row))
        for row in rows
        for number in range(1, seats_per_row + 1)
    ]


def seed() -> None:
    """Add every sample show (and its seats) that is not already in the database."""
    with SessionLocal() as db:
        try:
            for data in SAMPLE_SHOWS:
                already_there = db.scalar(select(Show).where(Show.title == data["title"]))
                if already_there:
                    print(f"Skipped (already exists): {data['title']}")
                    continue

                show = Show(
                    title=data["title"],
                    category=data["category"],
                    venue=data["venue"],
                    starts_at=data["starts_at"],
                )
                show.seats = build_seats(
                    data["rows"], data["seats_per_row"], data["price_for_row"]
                )
                db.add(show)
                print(f"Added: {show.title} ({len(show.seats)} seats)")

            db.commit()  # save everything together, or nothing
            print("Seeding finished.")
        except SQLAlchemyError as error:
            db.rollback()  # undo everything from this run
            print(f"Seeding failed, nothing was saved: {error}")
            sys.exit(1)


if __name__ == "__main__":
    seed()