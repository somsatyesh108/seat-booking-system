"""
seed_data.py - The sample catalogue for Bookify: made-up movies, bus routes and events in Bengaluru.

Each title can have several showtimes: (venue, start time).
Prices are in paise (Rs 150 = 15000).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def ist(month: int, day: int, hour: int, minute: int = 0) -> datetime:
    """A date and time in 2026, Indian time."""
    return datetime(2026, month, day, hour, minute, tzinfo=IST)


# Seat layouts: which rows, and how many seats per row.
LAYOUTS = {
    "cinema": {"rows": "ABCDEF", "per_row": 10},
    "bus": {"rows": "ABCDEFGHIJ", "per_row": 4},
    "arena": {"rows": "ABCDE", "per_row": 10},
}


def price_for(layout: str, base_price_paise: int, row: str) -> int:
    """Seat price by row: front rows cheaper in cinemas, VIP row A at events."""
    if layout == "cinema":
        if row in "AB":
            return base_price_paise
        if row == "F":
            return base_price_paise + 25000  # recliners
        return base_price_paise + 10000
    if layout == "arena" and base_price_paise > 0:
        return base_price_paise + 50000 if row == "A" else base_price_paise
    return base_price_paise


LUMIERE = "Lumiere Cinemas, Koramangala"
STARLIGHT = "Starlight Multiplex, Indiranagar"
SKYLINE = "Skyline Cinemas, Whitefield"
MAJESTIC = "Majestic Bus Stand, Bengaluru"

CATALOG = [
    # ---------------- Movies ----------------
    {
        "title": "The Last Monsoon", "category": "movie", "layout": "cinema", "base_price_paise": 15000,
        "language": "Kannada", "genre": "Drama", "duration_minutes": 142, "age_rating": "UA",
        "description": "A retired lorry driver and his granddaughter drive the old Mysuru road "
        "one last time before the family house is sold.",
        "showtimes": [
            ("Forum Mall Screen 3, Bengaluru", ist(12, 5, 19)),
            (STARLIGHT, ist(11, 21, 21, 30)),
            (LUMIERE, ist(11, 22, 16)),
        ],
    },
    {
        "title": "Orbit 9", "category": "movie", "layout": "cinema", "base_price_paise": 20000,
        "language": "English", "genre": "Sci-Fi, Thriller", "duration_minutes": 156, "age_rating": "UA",
        "description": "Nine engineers on a failing space station have eleven hours to decide "
        "who gets the only seats home.",
        "showtimes": [(LUMIERE, ist(11, 20, 18, 30)), (SKYLINE, ist(11, 21, 20)), (STARLIGHT, ist(12, 6, 22))],
    },
    {
        "title": "Silk Board Signal", "category": "movie", "layout": "cinema", "base_price_paise": 15000,
        "language": "Kannada", "genre": "Comedy", "duration_minutes": 118, "age_rating": "U",
        "description": "Four strangers stuck at the city's slowest traffic signal start a business "
        "before the light turns green.",
        "showtimes": [(STARLIGHT, ist(11, 20, 19)), (LUMIERE, ist(11, 23, 13))],
    },
    {
        "title": "Kaveri Calling", "category": "movie", "layout": "cinema", "base_price_paise": 18000,
        "language": "Tamil", "genre": "Action, Drama", "duration_minutes": 149, "age_rating": "UA",
        "description": "A river engineer returns home to stop a dam deal that would flood her village.",
        "showtimes": [(SKYLINE, ist(11, 22, 20, 30)), (STARLIGHT, ist(11, 28, 18))],
    },
    {
        "title": "The Filter Coffee Club", "category": "movie", "layout": "cinema", "base_price_paise": 15000,
        "language": "Hindi", "genre": "Comedy, Drama", "duration_minutes": 124, "age_rating": "U",
        "description": "Three retired friends reopen their old cafe in Malleswaram and accidentally go viral.",
        "showtimes": [(LUMIERE, ist(11, 21, 17)), (SKYLINE, ist(11, 29, 15, 30))],
    },
    {
        "title": "Nandi Hills at Dawn", "category": "movie", "layout": "cinema", "base_price_paise": 16000,
        "language": "Telugu", "genre": "Romance", "duration_minutes": 131, "age_rating": "U",
        "description": "Two cyclists meet on a 4 a.m. climb and keep meeting there, every Sunday, for a year.",
        "showtimes": [(SKYLINE, ist(11, 23, 10, 30)), (LUMIERE, ist(11, 30, 19, 30))],
    },
    # ---------------- Bus routes ----------------
    {
        "title": "Bengaluru to Chennai Night Express", "category": "bus", "layout": "bus",
        "base_price_paise": 80000, "genre": "AC Sleeper", "duration_minutes": 360,
        "description": "Overnight AC sleeper with charging points and one 20-minute stop at Krishnagiri.",
        "showtimes": [(MAJESTIC, ist(12, 6, 22, 30)), (MAJESTIC, ist(11, 21, 22, 30))],
    },
    {
        "title": "Bengaluru to Mysuru Morning Flyer", "category": "bus", "layout": "bus",
        "base_price_paise": 45000, "genre": "AC Seater", "duration_minutes": 180,
        "description": "Early departure that reaches Mysuru in time for breakfast near the palace.",
        "showtimes": [("Satellite Bus Stand, Mysuru Road", ist(11, 22, 6, 30)),
                      ("Satellite Bus Stand, Mysuru Road", ist(11, 29, 6, 30))],
    },
    {
        "title": "Bengaluru to Goa Coastal Sleeper", "category": "bus", "layout": "bus",
        "base_price_paise": 140000, "genre": "AC Sleeper", "duration_minutes": 660,
        "description": "Leave after work on Friday, wake up near the beach on Saturday morning.",
        "showtimes": [(MAJESTIC, ist(11, 27, 20))],
    },
    {
        "title": "Bengaluru to Hyderabad Express", "category": "bus", "layout": "bus",
        "base_price_paise": 95000, "genre": "AC Seater", "duration_minutes": 540,
        "description": "Reclining seats, blankets and a short dinner stop at Anantapur.",
        "showtimes": [(MAJESTIC, ist(11, 28, 21))],
    },
    # ---------------- Events ----------------
    {
        "title": "Indie Music Night", "category": "event", "layout": "arena", "base_price_paise": 99900,
        "language": "English", "genre": "Music", "duration_minutes": 180, "age_rating": "U",
        "description": "Five independent bands from Bengaluru and Shillong play one long evening under the trees.",
        "showtimes": [("Palace Grounds, Bengaluru", ist(12, 12, 18))],
    },
    {
        "title": "Stand-up Saturday", "category": "event", "layout": "arena", "base_price_paise": 49900,
        "language": "English", "genre": "Comedy", "duration_minutes": 120, "age_rating": "A",
        "description": "Six comics trying brand-new material. Phones stay in your pocket.",
        "showtimes": [("The Comedy Room, Indiranagar", ist(11, 21, 20)),
                      ("The Comedy Room, Indiranagar", ist(11, 28, 20))],
    },
    {
        "title": "Carnatic Evening by the Lake", "category": "event", "layout": "arena",
        "base_price_paise": 30000, "language": "Kannada", "genre": "Music", "duration_minutes": 150,
        "age_rating": "U",
        "description": "Violin, mridangam and voice at sunset, with the lake as the backdrop.",
        "showtimes": [("Lakeside Amphitheatre, Sankey Tank", ist(11, 23, 17, 30))],
    },
    {
        "title": "Startup Pitch Night", "category": "event", "layout": "arena", "base_price_paise": 0,
        "language": "English", "genre": "Talk", "duration_minutes": 150, "age_rating": "U",
        "description": "Ten early-stage founders, five minutes each, and a live audience vote. Free entry.",
        "showtimes": [("Tech Park Auditorium, Whitefield", ist(12, 3, 18, 30))],
    },
]