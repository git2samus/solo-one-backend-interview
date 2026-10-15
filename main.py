from fastapi import FastAPI

app = FastAPI(
    title="Meeting Notes API",
    description="API for managing meetings, notes, and tasks",
    version="1.0.0"
)

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


# Imported after `app` is defined: the views import `app` from this module
# and register their routes on it at import time.
from views.meetings import (  # noqa: E402, F401
    create_meeting,
    delete_meeting,
    get_meeting,
    list_meetings,
    update_meeting,
)
from views.notes import create_note, get_note, list_notes  # noqa: E402, F401
from views.tasks import (  # noqa: E402, F401
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)
from views.users import create_user, get_user, list_users  # noqa: E402, F401
