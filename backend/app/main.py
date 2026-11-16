"""
main.py - The starting point of our Seat Booking API.

Right now it has one endpoint: GET /health
Later we will add signup/login, shows, seats, holds and bookings.
"""

from fastapi import FastAPI

# Create the FastAPI application.
# Think of `app` as the restaurant itself: every endpoint we add
# below is a new item on its menu.
app = FastAPI(
    title="Seat Booking API",
    description="Concurrent seat booking system with Redis seat holds "
    "and PostgreSQL row locking to prevent double-booking.",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict:
    """
    A simple "are you alive?" check.

    Example: Som opens http://127.0.0.1:8000/health
    and gets back {"status": "ok"}.
    """
    return {"status": "ok"}
