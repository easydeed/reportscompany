from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional


class RLSContextMiddleware(BaseHTTPMiddleware):
    """
    Placeholder for Row-Level Security context.
    Later we'll decode JWT/API key and set:
      - request.state.account_id
      - Postgres: SET LOCAL app.current_account_id = '<uuid>';
    For now, accept 'X-Demo-Account' header to simulate an account context.
    """
    async def dispatch(self, request: Request, call_next):
        demo: Optional[str] = request.headers.get("X-Demo-Account")
        if demo:
            request.state.account_id = demo  # used later by DB layer
        response = await call_next(request)
        return response

