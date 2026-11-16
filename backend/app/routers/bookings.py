"""
routers/bookings.py - Turning seat holds into confirmed bookings, safely.

  POST /bookings      -> book the seats you are holding (all-or-nothing)
  GET  /bookings/me   -> your own bookings

Three layers stop double-booking:
  1. Redis hold:  you must hold every seat (SET NX EX gave it to only one person)
  2. Row lock:    SELECT ... FOR UPDATE makes other bookers of these seats WAIT
  3. Database:    UNIQUE(seat_id) on bookings rejects any duplicate that slips through
"""

import logging
from typing import Annotated

import redis
from fastapi import APIRouter, Depends, HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser
from app.holds import get_holders, release_hold
from app.models import Booking, Seat, Show
from app.redis_client import get_redis
from app.schemas import BookingConfirmation, BookingCreate, BookingOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["bookings"])

DbSession = Annotated[Session, Depends(get_db)]
RedisClient = Annotated[redis.Redis, Depends(get_redis)]


def _label(seat: Seat) -> str:
    return f"{seat.row_label}{seat.seat_number}"


def _to_out(booking: Booking, seat: Seat, show: Show) -> BookingOut:
    return BookingOut(
        id=booking.id,
        show_id=show.id,
        show_title=show.title,
        seat_id=seat.id,
        seat_label=_label(seat),
        amount_paise=booking.amount_paise,
        created_at=booking.created_at,
    )


@router.post("", response_model=BookingConfirmation, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate, current_user: CurrentUser, db: DbSession, r: RedisClient
) -> BookingConfirmation:
    """
    Book the seats you are holding. All-or-nothing: either every seat is booked, or none.

    Example: Som holds A1 and A2, then sends {"show_id": 1, "seat_ids": [1, 2]}
    -> 201 with both bookings and the total price.
    """
    # 1. The show must exist.
    show = db.get(Show, payload.show_id)
    if show is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Show not found.")

    # 2. Every seat must exist AND belong to this show.
    seats = list(
        db.scalars(
            select(Seat).where(Seat.show_id == show.id, Seat.id.in_(payload.seat_ids))
        )
    )
    if len(seats) != len(payload.seat_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more seats were not found in this show.",
        )

    # 3. LAYER 1: you must currently hold every seat in Redis.
    try:
        holders = get_holders(r, show.id, [seat.id for seat in seats])
    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Seat holds are temporarily unavailable. Please try again shortly.",
        ) from None

    not_held = sorted(_label(seat) for seat in seats if holders.get(seat.id) != current_user.id)
    if not_held:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Hold these seats before booking (holds last 5 minutes): {', '.join(not_held)}",
        )

    # 4. LAYER 2: lock the seat rows. Anyone else booking these seats now WAITS here
    #    until we commit or roll back. Locking in id order avoids deadlocks when two
    #    people book overlapping seats (e.g. Som books A1+A2 while Nahul books A2+A1).
    locked_seats = list(
        db.scalars(
            select(Seat)
            .where(Seat.id.in_(payload.seat_ids))
            .order_by(Seat.id)
            .with_for_update()
        )
    )

    already_booked = set(
        db.scalars(select(Booking.seat_id).where(Booking.seat_id.in_(payload.seat_ids)))
    )
    if already_booked:
        db.rollback()  # release the locks
        labels = sorted(_label(seat) for seat in locked_seats if seat.id in already_booked)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Already booked: {', '.join(labels)}",
        )

    bookings = [
        Booking(user_id=current_user.id, seat_id=seat.id, amount_paise=seat.price_paise)
        for seat in locked_seats
    ]
    db.add_all(bookings)

    # 5. LAYER 3: commit. UNIQUE(seat_id) is the last line of defense.
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="One of these seats was just booked by someone else.",
        ) from None

    for booking in bookings:
        db.refresh(booking)  # load id and created_at from PostgreSQL

    # 6. The seats are booked, so their holds are no longer needed.
    #    If Redis fails here, the booking is still safe; the holds simply expire on their own.
    for seat in locked_seats:
        try:
            release_hold(r, show.id, seat.id, current_user.id)
        except RedisError:
            logger.warning("Could not release hold for seat %s after booking", seat.id)

    seats_by_id = {seat.id: seat for seat in locked_seats}
    return BookingConfirmation(
        show_id=show.id,
        bookings=[_to_out(b, seats_by_id[b.seat_id], show) for b in bookings],
        total_paise=sum(b.amount_paise for b in bookings),
    )


@router.get("/me", response_model=list[BookingOut])
def my_bookings(current_user: CurrentUser, db: DbSession) -> list[BookingOut]:
    """All bookings of the logged-in user, newest first."""
    rows = db.execute(
        select(Booking, Seat, Show)
        .join(Seat, Booking.seat_id == Seat.id)
        .join(Show, Seat.show_id == Show.id)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc(), Booking.id.desc())
    ).all()
    return [_to_out(booking, seat, show) for booking, seat, show in rows]