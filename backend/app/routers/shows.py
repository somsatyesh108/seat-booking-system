"""
routers/shows.py - Shows, seat maps and 5-minute seat holds.

  GET    /shows?category=movie                    -> all showtimes, with seats left and lowest price
  GET    /shows/{show_id}                         -> one showtime, with seats left and lowest price
  GET    /shows/{show_id}/seats                   -> seat map (available / held / booked)
  POST   /shows/{show_id}/seats/{seat_id}/hold    -> hold a seat for 5 minutes (login needed)
  DELETE /shows/{show_id}/seats/{seat_id}/hold    -> release your own hold (login needed)
"""

from typing import Annotated, Literal

import redis
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import CurrentUser
from app.holds import get_holder, get_holders, release_hold, seconds_left, try_hold_seat
from app.models import Booking, Seat, Show
from app.redis_client import get_redis
from app.schemas import HoldOut, SeatMapOut, SeatOut, ShowListItem, ShowOut

router = APIRouter(prefix="/shows", tags=["shows"])

DbSession = Annotated[Session, Depends(get_db)]
RedisClient = Annotated[redis.Redis, Depends(get_redis)]
Category = Literal["movie", "bus", "event"]


# ---------- Small helpers ----------

def _get_show_or_404(db: Session, show_id: int) -> Show:
    show = db.get(Show, show_id)
    if show is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Show not found.")
    return show


def _get_seat_or_404(db: Session, show_id: int, seat_id: int) -> Seat:
    """The seat must exist AND belong to this show (seat 7 of show 1, not of show 2)."""
    seat = db.get(Seat, seat_id)
    if seat is None or seat.show_id != show_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Seat not found in this show."
        )
    return seat


def _redis_unavailable() -> HTTPException:
    """If Redis is down, say so clearly instead of crashing with a 500."""
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Seat holds are temporarily unavailable. Please try again shortly.",
    )


def _shows_with_stats(
    db: Session, category: str | None = None, show_id: int | None = None
) -> list[ShowListItem]:
    """
    Showtimes plus live numbers, in ONE database query:
    total seats, booked seats and the cheapest seat price for each show.
    """
    seat_stats = (
        select(
            Seat.show_id.label("show_id"),
            func.count(Seat.id).label("seats_total"),
            func.count(Booking.id).label("seats_booked"),  # counts only seats that HAVE a booking
            func.min(Seat.price_paise).label("min_price_paise"),
        )
        .outerjoin(Booking, Booking.seat_id == Seat.id)
        .group_by(Seat.show_id)
        .subquery()
    )

    query = (
        select(
            Show,
            seat_stats.c.seats_total,
            seat_stats.c.seats_booked,
            seat_stats.c.min_price_paise,
        )
        .outerjoin(seat_stats, seat_stats.c.show_id == Show.id)
        .order_by(Show.starts_at, Show.id)
    )
    if category is not None:
        query = query.where(Show.category == category)
    if show_id is not None:
        query = query.where(Show.id == show_id)

    return [
        ShowListItem(
            **ShowOut.model_validate(show).model_dump(),
            seats_total=total or 0,
            seats_booked=booked or 0,
            min_price_paise=min_price,
        )
        for show, total, booked, min_price in db.execute(query).all()
    ]


# ---------- Endpoints ----------

@router.get("", response_model=list[ShowListItem])
def list_shows(
    db: DbSession, category: Annotated[Category | None, Query()] = None
) -> list[ShowListItem]:
    """All showtimes, earliest first. Optional filter: ?category=movie (or bus, event)."""
    return _shows_with_stats(db, category=category)


@router.get("/{show_id}", response_model=ShowListItem)
def get_show(show_id: int, db: DbSession) -> ShowListItem:
    """One showtime's details, with seats left and the lowest price."""
    rows = _shows_with_stats(db, show_id=show_id)
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Show not found.")
    return rows[0]


@router.get("/{show_id}/seats", response_model=SeatMapOut)
def seat_map(show_id: int, db: DbSession, r: RedisClient) -> SeatMapOut:
    """
    The seat map for one show, with each seat's live status.

    Order of importance: booked (PostgreSQL) > held (Redis) > available.
    """
    show = _get_show_or_404(db, show_id)

    seats = list(
        db.scalars(
            select(Seat)
            .where(Seat.show_id == show_id)
            .order_by(Seat.row_label, Seat.seat_number)
        )
    )
    booked_seat_ids = set(
        db.scalars(select(Booking.seat_id).join(Seat).where(Seat.show_id == show_id))
    )

    try:
        holders = get_holders(r, show_id, [seat.id for seat in seats])  # one Redis trip
    except RedisError:
        raise _redis_unavailable() from None

    def status_of(seat: Seat) -> str:
        if seat.id in booked_seat_ids:
            return "booked"
        if seat.id in holders:
            return "held"
        return "available"

    return SeatMapOut(
        show=ShowOut.model_validate(show),
        seats=[
            SeatOut(
                id=seat.id,
                label=f"{seat.row_label}{seat.seat_number}",
                row_label=seat.row_label,
                seat_number=seat.seat_number,
                price_paise=seat.price_paise,
                status=status_of(seat),
            )
            for seat in seats
        ],
    )


@router.post(
    "/{show_id}/seats/{seat_id}/hold",
    response_model=HoldOut,
    status_code=status.HTTP_201_CREATED,
)
def hold_seat(
    show_id: int, seat_id: int, current_user: CurrentUser, db: DbSession, r: RedisClient
) -> HoldOut:
    """
    Hold a seat for 5 minutes so nobody else can take it while you pay.

    Som holds A7 -> 201. Nahul then tries A7 -> 409. Som clicks hold again -> 201 (kept, not extended).
    """
    seat = _get_seat_or_404(db, show_id, seat_id)
    label = f"{seat.row_label}{seat.seat_number}"

    if db.scalar(select(Booking.id).where(Booking.seat_id == seat.id)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Seat {label} is already booked."
        )

    try:
        got_it = try_hold_seat(r, show_id, seat.id, current_user.id)
        if not got_it and get_holder(r, show_id, seat.id) != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Seat {label} is being held by someone else. Try again in a few minutes.",
            )
        expires_in = seconds_left(r, show_id, seat.id)
    except RedisError:
        raise _redis_unavailable() from None

    return HoldOut(
        show_id=show_id,
        seat_id=seat.id,
        seat_label=label,
        held_by_user_id=current_user.id,
        expires_in_seconds=expires_in,
    )


@router.delete("/{show_id}/seats/{seat_id}/hold", status_code=status.HTTP_204_NO_CONTENT)
def release_seat_hold(
    show_id: int, seat_id: int, current_user: CurrentUser, db: DbSession, r: RedisClient
) -> Response:
    """Release your own hold early. Someone else's hold -> 404."""
    seat = _get_seat_or_404(db, show_id, seat_id)

    try:
        released = release_hold(r, show_id, seat.id, current_user.id)
    except RedisError:
        raise _redis_unavailable() from None

    if not released:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="You do not have a hold on this seat."
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)