"""
routers/auth.py - Signup (now), login and "who am I" (coming next).

All endpoints here start with /auth, e.g. POST /auth/signup
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut
from app.security import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """
    Create a new account.

    Example: Som sends {"email": "som@example.com", "full_name": "Som", "password": "som@1234"}
    -> 201 Created with his id, email, name and created_at (never the password).
    If the email is already registered -> 409 Conflict.
    """
    # Treat SOM@Example.com and som@example.com as the same email.
    email = payload.email.lower()

    # Friendly early check: is this email already taken?
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),  # store the hash, never the password
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        # Two signups with the same email at the SAME moment can both pass the check above.
        # The database's unique rule (ix_users_email) stops the second one; we turn that into a 409.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    db.refresh(user)  # load the id and created_at that PostgreSQL filled in
    return user