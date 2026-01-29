from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict

from fastapi import HTTPException


@dataclass
class RateLimitConfig:
    """Rate limiter config."""
    limit: int
    window_seconds: int


class InMemoryRateLimiter:
    """A simple in-memory rolling-window rate limiter.

    Note: This is per-process only. Replace with Redis for multi-replica deployments.
    """

    def __init__(self, config: RateLimitConfig):
        self._config = config
        self._events: Dict[str, Deque[float]] = defaultdict(deque)

    # PUBLIC_INTERFACE
    def check(self, key: str) -> None:
        """Check and consume one event for the given key.

        Raises:
            HTTPException: 429 if rate limited.
        """
        now = time.time()
        q = self._events[key]
        # evict expired
        while q and (now - q[0]) > self._config.window_seconds:
            q.popleft()
        if len(q) >= self._config.limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
        q.append(now)
