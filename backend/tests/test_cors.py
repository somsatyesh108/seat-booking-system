"""
test_cors.py - The browser rule (CORS): only our React app may call the API from a web page.
"""


def test_react_app_origin_is_allowed(client):
    """A browser asking 'may localhost:5173 call GET /shows?' gets a yes."""
    response = client.options(
        "/shows",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_unknown_website_is_not_allowed(client):
    """A random website does NOT get the permission header, so the browser blocks it."""
    response = client.get("/shows", headers={"Origin": "http://evil.example.com"})

    assert "access-control-allow-origin" not in response.headers