"""
main.py - The starting point of our Seat Booking API.

Right now it has one endpoint: GET /health
Later we will add signup/login, shows, seats, holds and bookings.
"""

from fastapi import FastAPI, Response, status

from app.database import check_database
from app.redis_client import check_redis

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
def health_check(response: Response) -> dict:
    """
    Check that the API, PostgreSQL and Redis are all working.

    Example: Som opens http://127.0.0.1:8000/health
    - Everything fine  -> 200 {"status": "ok", "database": "up", "redis": "up"}
    - Redis is stopped -> 503 {"status": "degraded", "database": "up", "redis": "down"}
    """
    database_ok = check_database()
    redis_ok = check_redis()
    all_ok = database_ok and redis_ok

    if not all_ok:
        # 503 = "Service Unavailable": tells monitoring tools something is wrong.
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if all_ok else "degraded",
        "database": "up" if database_ok else "down",
        "redis": "up" if redis_ok else "down",
    }
