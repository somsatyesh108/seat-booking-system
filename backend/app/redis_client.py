"""
redis_client.py - Connection to Redis.

Redis stores temporary 5-minute seat holds that expire automatically.
Every other file that needs Redis imports from here.
"""

import logging
from functools import lru_cache

import redis
from redis.exceptions import RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_redis() -> redis.Redis:
    """
    Create ONE Redis client and reuse it everywhere.

    The client keeps its own pool of connections inside, so sharing it is safe.
    """
    settings = get_settings()
    return redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,     # give us normal text ("user:som"), not bytes
        socket_connect_timeout=2,  # give up connecting after 2 seconds
        socket_timeout=2,          # give up waiting for a reply after 2 seconds
    )


def check_redis() -> bool:
    """Return True if Redis answers PING, otherwise False."""
    try:
        return bool(get_redis().ping())
    except RedisError as error:
        logger.warning("Redis health check failed: %s", error)
        return False
