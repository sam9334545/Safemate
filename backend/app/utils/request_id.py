"""Request ID tracking utilities for correlation without sensitive data retention."""

import uuid
from contextvars import ContextVar
from typing import Optional

_request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def generate_request_id() -> str:
    """Generate a unique request identifier."""
    return f"req_{uuid.uuid4().hex[:12]}"


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set the current request ID in context."""
    rid = request_id or generate_request_id()
    _request_id_ctx_var.set(rid)
    return rid


def get_request_id() -> str:
    """Get the active request ID or generate one if not present."""
    rid = _request_id_ctx_var.get()
    if not rid:
        rid = generate_request_id()
        _request_id_ctx_var.set(rid)
    return rid
