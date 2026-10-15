from typing import List

import schemas
from main import app


@app.post("/users/", response_model=schemas.User, status_code=201)
async def create_user(user: schemas.UserCreate):
    """
    Create a new user.
    """
    # Stub: Return a mock user
    return schemas.User(id=1, name=user.name, email=user.email)


@app.get("/users/", response_model=List[schemas.User])
async def list_users():
    """
    List all users.
    """
    # Stub: Return empty list
    return []


@app.get("/users/{user_id}", response_model=schemas.User)
async def get_user(user_id: int):
    """
    Get a specific user by ID.
    """
    # Stub: Return a mock user
    return schemas.User(id=user_id, name="John Doe", email="john@example.com")
