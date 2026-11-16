"""
test_auth.py - Tests for signup, login and "who am I" through the real API.

Uses the `client` fixture (conftest.py): every user created here is rolled back
after each test, so the real database (Arjun, sample shows) is never touched.
"""


# ---------- Small helpers ----------

def signup(client, name: str, password: str = "secret@123", email: str | None = None):
    """Sign up a test user like Som, Nahul or Priya through the API."""
    return client.post(
        "/auth/signup",
        json={
            "email": email or f"{name.lower()}@example.com",
            "full_name": name,
            "password": password,
        },
    )


def login(client, email: str, password: str):
    """Log in through the API using the standard OAuth2 form fields."""
    return client.post("/auth/login", data={"username": email, "password": password})


# ---------- Signup ----------

def test_signup_creates_user_and_never_returns_password(client):
    """Som signs up with a mixed-case email -> 201, email stored in lowercase."""
    response = signup(client, "Som", email="Som@Example.com")

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "som@example.com"
    assert body["full_name"] == "Som"
    assert "id" in body and "created_at" in body
    assert "password" not in body
    assert "hashed_password" not in body


def test_signup_with_existing_email_is_rejected(client):
    """Som signs up twice with the same email -> second attempt gets 409."""
    assert signup(client, "Som").status_code == 201

    response = signup(client, "Som")

    assert response.status_code == 409
    assert response.json()["detail"] == "An account with this email already exists."


def test_signup_with_bad_input_is_rejected(client):
    """Bad email and a 3-character password -> 422 listing both problems."""
    response = client.post(
        "/auth/signup",
        json={"email": "not-an-email", "full_name": "Nahul", "password": "123"},
    )

    assert response.status_code == 422
    problem_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert {"email", "password"} <= problem_fields


# ---------- Login ----------

def test_login_with_correct_password_returns_token(client):
    """Nahul logs in with the right password -> 200 and a bearer token."""
    signup(client, "Nahul", password="nahul@1234")

    response = login(client, "nahul@example.com", "nahul@1234")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].startswith("eyJ")


def test_login_with_wrong_password_is_rejected(client):
    """Nahul types the wrong password -> 401."""
    signup(client, "Nahul", password="nahul@1234")

    response = login(client, "nahul@example.com", "wrong-password")

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


def test_login_with_unknown_email_gives_same_error(client):
    """An email that was never registered -> exactly the same 401 as a wrong password."""
    response = login(client, "nobody@example.com", "whatever123")

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


# ---------- Who am I ----------

def test_me_returns_the_logged_in_user(client):
    """Priya logs in and asks /auth/me -> her own details."""
    signup(client, "Priya", password="priya@1234")
    token = login(client, "priya@example.com", "priya@1234").json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "priya@example.com"
    assert response.json()["full_name"] == "Priya"


def test_me_without_token_is_rejected(client):
    """No Authorization header at all -> 401 Not authenticated."""
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_me_with_fake_token_is_rejected(client):
    """A made-up token -> 401 Could not validate credentials."""
    response = client.get("/auth/me", headers={"Authorization": "Bearer fake.token.here"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."