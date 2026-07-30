"""
ThreatLens AI - Security Middleware
Request validation, security headers, and request logging.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging

logger = logging.getLogger("threatlens")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        if not request.url.path.startswith("/docs"):
            response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests for audit trail."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"REQUEST | {request.method} {request.url.path} | "
            f"Client: {client_ip} | "
            f"User-Agent: {request.headers.get('user-agent', 'unknown')[:80]}"
        )

        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info(
            f"RESPONSE | {request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration:.3f}s"
        )

        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests for basic security checks."""

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

    async def dispatch(self, request: Request, call_next):
        # Check content length for upload endpoints
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
                return Response(
                    content='{"detail": "Request body too large"}',
                    status_code=413,
                    media_type="application/json",
                )

        return await call_next(request)
