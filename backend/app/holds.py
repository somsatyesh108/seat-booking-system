"""
holds.py - Temporary seat holds stored in Redis (auto-expire after 5 minutes).

One Redis key per held seat:
    key   = "hold:show:{show_id}:seat:{seat_id}"
    value = the id of the user holding it
Example: Som (user 31) holds seat 7 of show 1 -> "hold:show:1:seat:7" = "31", expires in 300s
"""

import redis

from app.config import get_settings


def hold_key(show_id: int, seat_id: int) -> str:
    """The Redis key name for one seat's hold."""
    return f"hold:show:{show_id}:seat:{seat_id}"


def try_hold_seat(r: redis.Redis, show_id: int, seat_id: int, user_id: int) -> bool:
    """
    Try to hold a seat for 5 minutes. Returns True if WE got it, False if someone else has it.

    SET ... NX EX is ATOMIC: Redis checks "is it free?" and sets it in ONE step,
    so if Som and Nahul click at the same millisecond, only one of them can win.
    """
    created = r.set(
        hold_key(show_id, seat_id),
        str(user_id),
        nx=True,  # only set if the key does NOT exist yet
        ex=get_settings().seat_hold_seconds,  # auto-delete after 300 seconds
    )
    return bool(created)


def get_holder(r: redis.Redis, show_id: int, seat_id: int) -> int | None:
    """Who is holding this seat right now? Returns a user id, or None if free."""
    value = r.get(hold_key(show_id, seat_id))
    return int(value) if value is not None else None


def seconds_left(r: redis.Redis, show_id: int, seat_id: int) -> int:
    """Seconds until this hold expires (0 if there is no hold)."""
    ttl = r.ttl(hold_key(show_id, seat_id))
    return max(ttl, 0)  # Redis returns -2 for "no such key", -1 for "no expiry"


def get_holders(r: redis.Redis, show_id: int, seat_ids: list[int]) -> dict[int, int]:
    """
    Holders for MANY seats in ONE Redis round trip (used by the seat map).

    Returns {seat_id: user_id} for held seats only.
    """
    if not seat_ids:
        return {}
    values = r.mget([hold_key(show_id, seat_id) for seat_id in seat_ids])
    return {
        seat_id: int(value)
        for seat_id, value in zip(seat_ids, values)
        if value is not None
    }


# Runs INSIDE Redis as one atomic step: delete the hold only if it belongs to this user.
_RELEASE_IF_OWNER = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


def release_hold(r: redis.Redis, show_id: int, seat_id: int, user_id: int) -> bool:
    """
    Release a hold early, but ONLY if this user owns it.

    Returns True if released. Nahul can never release Som's hold.
    """
    deleted = r.eval(_RELEASE_IF_OWNER, 1, hold_key(show_id, seat_id), str(user_id))
    return deleted == 1