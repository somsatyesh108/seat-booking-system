"""
seed.py - Fills the database with the sample catalogue from seed_data.py.

Run from the backend folder with:  python -m app.seed
Safe to run many times: an existing showtime (same title + start time) is never duplicated;
only its details (genre, language, description...) are refreshed.
"""

import sys

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import Seat, Show
from app.seed_data import CATALOG, LAYOUTS, price_for


def build_seats(layout_name: str, base_price_paise: int) -> list[Seat]:
    """Create Seat objects like A1, A2, ... for every row of the layout."""
    layout = LAYOUTS[layout_name]
    return [
        Seat(
            row_label=row,
            seat_number=number,
            price_paise=price_for(layout_name, base_price_paise, row),
        )
        for row in layout["rows"]
        for number in range(1, layout["per_row"] + 1)
    ]


def details_of(item: dict) -> dict:
    """The descriptive fields shared by every showtime of one title."""
    return {
        "category": item["category"],
        "description": item.get("description", ""),
        "genre": item.get("genre", ""),
        "language": item.get("language", ""),
        "duration_minutes": item.get("duration_minutes"),
        "age_rating": item.get("age_rating", ""),
    }


def seed() -> None:
    created = refreshed = 0
    with SessionLocal() as db:
        try:
            for item in CATALOG:
                details = details_of(item)
                for venue, starts_at in item["showtimes"]:
                    existing = db.scalar(
                        select(Show).where(Show.title == item["title"], Show.starts_at == starts_at)
                    )
                    if existing:
                        for field, value in details.items():
                            setattr(existing, field, value)
                        refreshed += 1
                        continue

                    show = Show(title=item["title"], venue=venue, starts_at=starts_at, **details)
                    show.seats = build_seats(item["layout"], item["base_price_paise"])
                    db.add(show)
                    created += 1

            db.commit()  # save everything together, or nothing
            print(f"Seeding finished: {created} new showtimes, {refreshed} existing showtimes refreshed.")
        except SQLAlchemyError as error:
            db.rollback()
            print(f"Seeding failed, nothing was saved: {error}")
            sys.exit(1)


if __name__ == "__main__":
    seed()