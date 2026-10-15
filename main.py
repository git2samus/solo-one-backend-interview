from fastapi import FastAPI

from views import meetings, notes, tasks, users

app = FastAPI(
    title="Meeting Notes API",
    description="API for managing meetings, notes, and tasks",
    version="1.0.0"
)

app.include_router(users.router)
app.include_router(meetings.router)
app.include_router(notes.router)
app.include_router(tasks.router)


@app.get("/")
async def root():
    """
    Root endpoint to verify the API is running.
    """
    return {
        "message": "Welcome to the Meeting Notes API",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users/",
            "meetings": "/meetings/",
            "notes": "/notes/",
            "tasks": "/tasks/"
        }
    }

