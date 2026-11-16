"""
main.py - The starting point of our Seat Booking API.

Endpoints:
  GET    /health
  POST   /auth/signup, POST /auth/login, GET /auth/me
  GET    /shows, GET /shows/{id}/seats
  POST   /shows/{id}/seats/{seat_id}/hold, DELETE /shows/{id}/seats/{seat_id}/hold
  POST   /bookings, GET /bookings/me
"""

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.database import check_database
from app.redis_client import check_redis
from app.routers import auth, bookings, shows

# Create the FastAPI application.
app = FastAPI(
    title="Seat Booking API",
    description="Concurrent seat booking system with Redis seat holds "
    "and PostgreSQL row locking to prevent double-booking.",
    version="0.1.0",
)

# CORS: browsers only let a web page read our API's replies if we trust the page's address.
# We trust ONLY our React app during development (Vite runs it on port 5173).
FRONTEND_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,  # we send the JWT in a header, not in cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plug in the groups of endpoints.
app.include_router(auth.router)
app.include_router(shows.router)
app.include_router(bookings.router)


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