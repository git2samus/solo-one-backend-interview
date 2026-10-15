from typing import List

import models
import schemas
from services.base import BaseService, ConflictError


class UserService(BaseService):
    name = "users"

    def create(self, data: schemas.UserCreate) -> schemas.User:
        existing = self.db.query(models.User).filter(models.User.email == data.email).first()
        if existing is not None:
            raise ConflictError(f"User with email {data.email} already exists")
        user = self._save(models.User(**data.model_dump()))
        return schemas.User.model_validate(user)

    def list(self) -> List[schemas.User]:
        users = self.db.query(models.User).order_by(models.User.id)
        return [schemas.User.model_validate(user) for user in users]

    def get(self, user_id: int) -> schemas.User:
        return schemas.User.model_validate(self._get_model(models.User, user_id))
