from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

USER_ID_HEADER = "X-User-ID"


class UserIdMiddleware(BaseHTTPMiddleware):
    """
    Read the user id from the request header and store it on request.state.user_id.

    A missing header leaves user_id as None; endpoints that require a user
    enforce that through the get_current_user_id dependency.
    """

    async def dispatch(self, request: Request, call_next):
        user_id: Optional[int] = None
        raw = request.headers.get(USER_ID_HEADER)
        if raw is not None:
            try:
                user_id = int(raw)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"{USER_ID_HEADER} header must be an integer"},
                )
        request.state.user_id = user_id
        return await call_next(request)


def get_current_user_id(request: Request) -> int:
    """
    Dependency that returns the user id extracted by UserIdMiddleware.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail=f"Missing {USER_ID_HEADER} header")
    return user_id
