"""Services module for external APIs."""
from .gmail_service import (
    get_gmail_service,
    fetch_unread_emails,
    send_email,
    mark_as_read
)

__all__ = [
    'get_gmail_service',
    'fetch_unread_emails',
    'send_email',
    'mark_as_read'
]
