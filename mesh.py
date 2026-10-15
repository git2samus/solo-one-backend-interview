from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from middleware import get_current_user_id
from services import SERVICE_CLASSES, BaseService


class Transport(ABC):
    """
    Delivers a call from the mesh to a service.

    Implementations decide the communication mode (in-process, gRPC, ...);
    callers only ever see ServiceMesh, so transports are interchangeable.
    """

    @abstractmethod
    def call(self, service: str, method: str, *args: Any, **kwargs: Any) -> Any:
        ...


class LocalTransport(Transport):
    """
    In-process transport: calls service instances living in this process.
    """

    def __init__(self, services: Dict[str, BaseService]):
        self._services = services

    def call(self, service: str, method: str, *args: Any, **kwargs: Any) -> Any:
        if service not in self._services:
            raise AttributeError(f"Unknown service: {service}")
        return getattr(self._services[service], method)(*args, **kwargs)


class ServiceProxy:
    """
    Stand-in for a single service; turns method calls into transport calls.
    """

    def __init__(self, transport: Transport, service: str):
        self._transport = transport
        self._service = service

    def __getattr__(self, method: str) -> Callable[..., Any]:
        if method.startswith("_"):
            raise AttributeError(method)

        def call(*args: Any, **kwargs: Any) -> Any:
            return self._transport.call(self._service, method, *args, **kwargs)

        return call


class ServiceMesh:
    """
    User-scoped entry point to all services: mesh.<service>.<method>(...).

    user_id is None for an anonymous mesh, which can only be used for calls
    that need no user (e.g. creating a user).
    """

    def __init__(self, user_id: Optional[int], transport: Optional[Transport] = None):
        self.user_id = user_id
        self._transport = transport

    def connect(self, transport: Transport) -> None:
        self._transport = transport

    def __getattr__(self, service: str) -> ServiceProxy:
        if service.startswith("_"):
            raise AttributeError(service)
        if self._transport is None:
            raise RuntimeError("ServiceMesh has no transport connected")
        return ServiceProxy(self._transport, service)


def build_local_mesh(db: Session, user_id: Optional[int]) -> ServiceMesh:
    """
    Build a mesh whose services run in-process against the given DB session.
    """
    mesh = ServiceMesh(user_id)
    services = {cls.name: cls(db=db, user_id=user_id, mesh=mesh) for cls in SERVICE_CLASSES}
    mesh.connect(LocalTransport(services))
    return mesh


def get_mesh(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ServiceMesh:
    """
    Dependency providing a service mesh bound to the requesting user.
    """
    if db.get(models.User, user_id) is None:
        raise HTTPException(status_code=401, detail=f"Unknown user {user_id}")
    return build_local_mesh(db, user_id)


def get_anonymous_mesh(db: Session = Depends(get_db)) -> ServiceMesh:
    """
    Dependency providing a mesh with no user, for endpoints that don't require one.
    """
    return build_local_mesh(db, user_id=None)
