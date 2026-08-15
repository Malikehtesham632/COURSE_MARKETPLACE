"""
A custom application exception.

Used for domain-specific rule violations (like "you can't buy your own
course") instead of a generic HTTPException, so these errors are easy
to tell apart from ordinary "not found" / "unauthorized" errors.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Raised when a business rule specific to this app is broken."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Turns an AppException into a clean, consistent JSON error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )
