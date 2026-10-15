from typing import Optional

from fastapi import HTTPException, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware

from settings import settings

# Declares the header as a security scheme so Swagger UI's "Authorize" button
# can send it; the value itself is read by UserIdMiddleware.
user_id_scheme = APIKeyHeader(
    name=settings.user_id_header,
    auto_error=False,
    description="ID of the user making the request. Create a user with POST /users/ first.",
)


class UserIdMiddleware(BaseHTTPMiddleware):
    """
    Read the user id from the request header and store it on request.state.user_id.

    A missing header leaves user_id as None; endpoints that require a user
    enforce that through the get_current_user_id dependency.
    """

    async def dispatch(self, request: Request, call_next):
        user_id: Optional[int] = None
        raw = request.headers.get(settings.user_id_header)
        if raw is not None:
            try:
                user_id = int(raw)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"{settings.user_id_header} header must be an integer"},
                )
        request.state.user_id = user_id
        return await call_next(request)


def get_current_user_id(request: Request, _: Optional[str] = Security(user_id_scheme)) -> int:
    """
    Dependency that returns the user id extracted by UserIdMiddleware.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise HTTPException(status_code=401, detail=f"Missing {settings.user_id_header} header")
    return user_id
