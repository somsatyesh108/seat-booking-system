"""
routers/auth.py - Signup, login and "who am I".

All endpoints here start with /auth:
  POST /auth/signup  -> create an account
  POST /auth/login   -> get a JWT access token
  GET  /auth/me      -> details of the logged-in user (requires a token)
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser
from app.models import User
from app.schemas import Token, UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

# A throwaway hash used when the email does not exist (see login() for why).
_DUMMY_HASH = hash_password("timing-attack-protection-dummy-password")


def _invalid_credentials() -> HTTPException:
    """The SAME error for 'no such email' and 'wrong password' (don't reveal which)."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )


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


@router.post("/login", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    """
    Log in with email + password and get a JWT access token.

    The form field is called "username" (an OAuth2 standard), but we put the EMAIL in it.
    Example: username=arjun@example.com, password=arjun@1234
    -> 200 {"access_token": "eyJ...", "token_type": "bearer"}
    Wrong email OR wrong password -> 401 with the same message.
    """
    email = form.username.strip().lower()
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        # Still do a full password check against a dummy hash, so a missing email
        # takes the same time as a wrong password. Otherwise attackers could time
        # the replies to discover which emails are registered.
        verify_password(form.password, _DUMMY_HASH)
        raise _invalid_credentials()

    if not verify_password(form.password, user.hashed_password):
        raise _invalid_credentials()

    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def read_me(current_user: CurrentUser) -> User:
    """
    Return the logged-in user's own details.

    Example: Arjun sends "Authorization: Bearer <his token>"
    -> 200 {"id": 31, "email": "arjun@example.com", "full_name": "Arjun", ...}
    No token, or a bad/expired token -> 401.
    """
    return current_user