"""
models.py - Our database tables, written as Python classes.

Each class = one table. Each attribute = one column.
Tables: users, shows, seats, bookings.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """
    A person who can sign up, log in and book seats.

    Example row: id=1, email="som@example.com", full_name="Som"
    """

    __tablename__ = "users"

    # Primary key: a unique number for every user (1, 2, 3, ...), set automatically.
    id: Mapped[int] = mapped_column(primary_key=True)

    # Email used to log in. unique=True: no two users can share an email.
    # index=True: makes "find user by email" fast during login.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    full_name: Mapped[str] = mapped_column(String(100))

    # We NEVER store the real password, only a scrambled (hashed) version.
    hashed_password: Mapped[str] = mapped_column(String(255))

    # Filled automatically by PostgreSQL with the current time.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Python shortcut: some_user.bookings gives all of this user's bookings.
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class Show(Base):
    """
    One showing people book seats for: a movie screening, a bus trip or an event.

    Example row: id=1, title="The Last Monsoon", category="movie", language="Kannada",
                 genre="Drama", duration_minutes=142, age_rating="UA",
                 venue="Forum Mall Screen 3, Bengaluru", starts_at=2026-12-05 19:00 IST
    The same title can have several rows (different times or venues) = several showtimes.
    """

    __tablename__ = "shows"

    # The database itself refuses any category other than these three.
    __table_args__ = (
        CheckConstraint(
            "category IN ('movie', 'bus', 'event')",
            name="ck_shows_category_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(20))
    venue: Mapped[str] = mapped_column(String(200))

    # When the show starts. index=True: makes "upcoming shows" lists fast.
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # ---- Details shown on the website (older rows get empty values) ----
    description: Mapped[str] = mapped_column(Text, server_default="")
    genre: Mapped[str] = mapped_column(String(60), server_default="")       # "Drama, Thriller"
    language: Mapped[str] = mapped_column(String(40), server_default="")    # "Kannada"
    duration_minutes: Mapped[int | None] = mapped_column(Integer)          # 142, or None
    age_rating: Mapped[str] = mapped_column(String(10), server_default="")  # "U", "UA", "A"

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Python shortcut: some_show.seats gives the list of this show's seats.
    # cascade: deleting a show also deletes its seats.
    seats: Mapped[list["Seat"]] = relationship(
        back_populates="show", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Show id={self.id} title={self.title!r} category={self.category!r}>"


class Seat(Base):
    """
    One seat for one show.

    Example row: id=7, show_id=1, row_label="A", seat_number=2, price_paise=25000
    means: seat A2 of show 1, costing Rs 250.00
    """

    __tablename__ = "seats"

    __table_args__ = (
        # The same show cannot have two "A2" seats.
        UniqueConstraint(
            "show_id", "row_label", "seat_number", name="uq_seats_show_row_number"
        ),
        CheckConstraint("seat_number > 0", name="ck_seats_number_positive"),
        CheckConstraint("price_paise >= 0", name="ck_seats_price_not_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Foreign key: this seat belongs to the show with this id.
    show_id: Mapped[int] = mapped_column(
        ForeignKey("shows.id", ondelete="CASCADE"), index=True
    )

    row_label: Mapped[str] = mapped_column(String(5))   # "A", "B", ...
    seat_number: Mapped[int] = mapped_column(Integer)   # 1, 2, 3, ...

    # Money as whole paise (Rs 250.00 = 25000) to avoid decimal rounding errors.
    price_paise: Mapped[int] = mapped_column(Integer)

    # Python shortcut: some_seat.show gives the Show this seat belongs to.
    show: Mapped["Show"] = relationship(back_populates="seats")

    # Python shortcut: some_seat.booking gives its Booking, or None if the seat is free.
    booking: Mapped["Booking | None"] = relationship(back_populates="seat")

    def __repr__(self) -> str:
        return f"<Seat id={self.id} show_id={self.show_id} {self.row_label}{self.seat_number}>"


class Booking(Base):
    """
    A confirmed booking: one user owns one seat.

    Example row: id=1, user_id=1 (Som), seat_id=7 (seat A2), amount_paise=25000

    THE DOUBLE-BOOKING GUARD:
    seat_id is UNIQUE, so PostgreSQL rejects a second booking for the same seat,
    even if two requests (Som and Nahul) arrive at exactly the same moment.
    """

    __tablename__ = "bookings"

    __table_args__ = (
        UniqueConstraint("seat_id", name="uq_bookings_seat_id"),
        CheckConstraint("amount_paise >= 0", name="ck_bookings_amount_not_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # Who booked. index=True: "show me Priya's bookings" is fast.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Which seat. If the seat is deleted (because its show was deleted), the booking goes too.
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id", ondelete="CASCADE"))

    # Price at the moment of booking (seat prices could change later).
    amount_paise: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="bookings")
    seat: Mapped["Seat"] = relationship(back_populates="booking")

    def __repr__(self) -> str:
        return f"<Booking id={self.id} user_id={self.user_id} seat_id={self.seat_id}>"