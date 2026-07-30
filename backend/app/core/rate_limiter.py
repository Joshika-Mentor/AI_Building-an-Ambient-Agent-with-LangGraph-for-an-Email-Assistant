"""
ThreatLens AI - Rate Limiter Middleware
Sliding window rate limiting using Redis.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.database import redis_client
import time


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis sliding window.
    Applies different limits based on endpoint path prefixes.
    """

    # Rate limit rules: (prefix, max_requests, window_seconds)
    RATE_LIMITS = [
        ("/api/v1/auth", 10, 60),       # 10 requests per minute for auth
        ("/api/v1/files/upload", 10, 60), # 10 uploads per minute
        ("/api/v1", 120, 60),             # 120 requests per minute general
    ]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting if Redis is not available
        if redis_client is None:
            return await call_next(request)

        # Determine client identifier
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Find applicable rate limit
        max_requests, window = self._get_limit(path)

        # Build Redis key
        key = f"rate_limit:{client_ip}:{path.split('/')[3] if len(path.split('/')) > 3 else 'general'}"

        try:
            # Sliding window counter
            current_time = int(time.time())
            window_start = current_time - window

            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zcard(key)
            pipe.expire(key, window)
            results = await pipe.execute()

            request_count = results[2]

            # Add rate limit headers to response
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - request_count))
            response.headers["X-RateLimit-Reset"] = str(current_time + window)

            if request_count > max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                )

            return response

        except HTTPException:
            raise
        except Exception:
            # If Redis fails, allow the request through
            return await call_next(request)

    def _get_limit(self, path: str) -> tuple:
        """Get the rate limit for a given path."""
        for prefix, max_req, window in self.RATE_LIMITS:
            if path.startswith(prefix):
                return max_req, window
        return 120, 60  # Default: 120/minute
