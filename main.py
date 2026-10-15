from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from database import create_tables
from middleware import UserIdMiddleware
from services import ConflictError, ForbiddenError, NotFoundError
from settings import settings
from views import meetings, notes, tasks, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(UserIdMiddleware)

app.include_router(users.router)
app.include_router(meetings.router)
app.include_router(notes.router)
app.include_router(tasks.router)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.get("/")
async def root():
    """
    Root endpoint to verify the API is running.
    """
    return {
        "message": f"Welcome to the {settings.app_title}",
        "version": settings.app_version,
        "endpoints": {
            "users": "/users/",
            "meetings": "/meetings/",
            "notes": "/notes/",
            "tasks": "/tasks/"
        }
    }

