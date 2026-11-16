"""
test_health.py - Automated tests for the GET /health endpoint.

Run from the backend folder with:  pytest -v
Note: test 1 needs Docker running (it uses the real PostgreSQL and Redis).
"""

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app

# TestClient acts like a browser: it calls our API without starting a server.
client = TestClient(app)


def test_health_returns_ok_when_database_and_redis_are_up():
    """Som checks /health while everything is running -> 200 and all 'up'."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up", "redis": "up"}


def test_health_returns_503_when_redis_is_down(monkeypatch):
    """Nahul checks /health while Redis is down -> 503 and redis 'down'."""
    # Pretend Redis is down by replacing check_redis with a fake that returns False.
    monkeypatch.setattr(main_module, "check_redis", lambda: False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "up", "redis": "down"}


def test_health_returns_503_when_database_is_down(monkeypatch):
    """Priya checks /health while PostgreSQL is down -> 503 and database 'down'."""
    # Pretend PostgreSQL is down.
    monkeypatch.setattr(main_module, "check_database", lambda: False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down", "redis": "up"}
