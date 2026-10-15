from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from mesh import ServiceMesh


class ServiceError(Exception):
    """
    Base class for errors raised by services; transport-agnostic so they can
    be re-raised on the caller side of any transport.
    """


class NotFoundError(ServiceError):
    def __init__(self, resource: str, resource_id: int):
        super().__init__(f"{resource} {resource_id} not found")


class ConflictError(ServiceError):
    pass


class ForbiddenError(ServiceError):
    pass


class BaseService(ABC):
    """
    Base class for all resource services.

    Services are bound to the user making the request (user_id is None only
    for anonymous calls such as sign-up) and must only expose that user's
    resources. They must use self.mesh (never another service directly) to
    call other services.
    """

    name: str

    def __init__(self, db: Session, user_id: Optional[int], mesh: "ServiceMesh"):
        self.db = db
        self.user_id = user_id
        self.mesh = mesh

    @abstractmethod
    def create(self, data: Any) -> Any:
        ...

    @abstractmethod
    def list(self, **filters: Any) -> List[Any]:
        ...

    @abstractmethod
    def get(self, resource_id: int) -> Any:
        ...

    def update(self, resource_id: int, data: Any) -> Any:
        raise NotImplementedError(f"{self.name} does not support update")

    def delete(self, resource_id: int) -> None:
        raise NotImplementedError(f"{self.name} does not support delete")

    def _get_model(self, model: type, resource_id: int) -> Any:
        instance = self.db.get(model, resource_id)
        if instance is None:
            raise NotFoundError(model.__name__, resource_id)
        return instance

    def _save(self, instance: Any) -> Any:
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
