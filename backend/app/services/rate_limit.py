import hashlib
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request, status

from app.config import Settings


class SessionRateLimiter:
    def __init__(self, settings: Settings):
        self.max_attempts = settings.session_rate_limit_attempts
        self.window_seconds = settings.session_rate_limit_window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for", "")
        ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:16]

    def check(self, request: Request) -> None:
        key = self._client_key(request)
        now = time.time()
        with self._lock:
            bucket = self._events[key]
            while bucket and now - bucket[0] > self.window_seconds:
                bucket.popleft()
            if len(bucket) >= self.max_attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many sign-in attempts. Please wait and try again.",
                )
            bucket.append(now)


_limiter: SessionRateLimiter | None = None


def get_session_rate_limiter(settings: Settings) -> SessionRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = SessionRateLimiter(settings)
    return _limiter
