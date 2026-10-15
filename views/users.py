from typing import List

from fastapi import APIRouter, Depends

import schemas
from mesh import ServiceMesh, get_mesh

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=schemas.User, status_code=201)
def create_user(user: schemas.UserCreate, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Create a new user.
    """
    return mesh.users.create(user)


@router.get("/", response_model=List[schemas.User])
def list_users(mesh: ServiceMesh = Depends(get_mesh)):
    """
    List all users.
    """
    return mesh.users.list()


@router.get("/{user_id}", response_model=schemas.User)
def get_user(user_id: int, mesh: ServiceMesh = Depends(get_mesh)):
    """
    Get a specific user by ID.
    """
    return mesh.users.get(user_id)
