"""
schemas.py - The shapes of data going IN to and OUT of our API.

These are Pydantic models (not database tables). FastAPI uses them to:
  - reject bad input automatically (wrong email, short password)
  - control exactly what we send back (never the password hash!)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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