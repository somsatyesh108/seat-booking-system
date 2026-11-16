"""
dependencies.py - Reusable "checks" that endpoints can ask for.

get_current_user: reads the "Authorization: Bearer <token>" header,
checks the token, and returns the logged-in User. Otherwise -> 401.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import TokenError, decode_access_token

# Tells FastAPI (and the /docs "Authorize" button) where users log in to get a token.
# If a request has NO token at all, this automatically replies 401 "Not authenticated".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Find out WHO is making this request.

    Example: Arjun sends "Authorization: Bearer eyJhbGciOi..." -> returns Arjun's User.
    Fake, edited or expired token, or the user no longer exists -> 401.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = decode_access_token(token)
    except TokenError:
        raise unauthorized from None

    user = db.get(User, user_id)  # look up the user by id
    if user is None:
        raise unauthorized  # token was valid, but this account no longer exists

    return user


# Shortcut: any endpoint can write `current_user: CurrentUser` to require login.
CurrentUser = Annotated[User, Depends(get_current_user)]