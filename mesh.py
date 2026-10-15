from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set, Tuple

from fastapi import Depends, HTTPException
from pydantic_core import to_jsonable_python
from sqlalchemy.orm import Session

import models
from cache import CacheBackend, InMemoryCache, cache_policy
from database import get_db
from middleware import get_current_user_id
from services import SERVICE_CLASSES, BaseService
from tools import Tool, collect_tools


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


class CachingTransport(Transport):
    """
    Wraps another transport, caching reads per user and invalidating on writes.

    Reads are the methods marked with @cached; every other call is a write,
    which invalidates the cached entries (of all users) that read the written
    service. Mesh calls made while computing a read are recorded as
    dependencies of that read.
    """

    def __init__(
        self,
        inner: Transport,
        cache: CacheBackend,
        user_id: Optional[int],
        policy: Dict[Tuple[str, str], FrozenSet[str]],
    ):
        self._inner = inner
        self._cache = cache
        self._user_id = user_id
        self._policy = policy
        self._reads_in_progress: List[Set[str]] = []

    def call(self, service: str, method: str, *args: Any, **kwargs: Any) -> Any:
        tags = self._policy.get((service, method))
        if tags is None:
            try:
                return self._inner.call(service, method, *args, **kwargs)
            finally:
                self._cache.invalidate({service})

        key = (self._user_id, service, method, args, tuple(sorted(kwargs.items())))
        entry = self._cache.get(key)
        if entry is not None:
            value, tags = entry
            self._record_dependencies(tags)
            return value

        version = self._cache.version()
        self._reads_in_progress.append(set(tags))
        try:
            value = self._inner.call(service, method, *args, **kwargs)
        finally:
            tags = frozenset(self._reads_in_progress.pop())
        self._cache.set(key, value, tags, version)
        self._record_dependencies(tags)
        return value

    def _record_dependencies(self, tags: FrozenSet[str]) -> None:
        if self._reads_in_progress:
            self._reads_in_progress[-1].update(tags)


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

    def __init__(
        self,
        user_id: Optional[int],
        transport: Optional[Transport] = None,
        tools: Optional[Dict[str, Tool]] = None,
    ):
        self.user_id = user_id
        self._transport = transport
        self._tools = tools or {}

    def connect(self, transport: Transport) -> None:
        self._transport = transport

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Definitions of the services' tools, ready to pass to an LLM.
        """
        return [tool.definition() for tool in self._tools.values()]

    def call_tool(self, name: str, tool_input: Dict[str, Any]) -> Any:
        """
        Run a tool call requested by an LLM through this mesh, so it is scoped
        to this mesh's user; returns a JSON-compatible result.
        """
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        tool = self._tools[name]
        result = getattr(getattr(self, tool.service), tool.method)(**tool.arguments(tool_input))
        return to_jsonable_python(result)

    def __getattr__(self, service: str) -> ServiceProxy:
        if service.startswith("_"):
            raise AttributeError(service)
        if self._transport is None:
            raise RuntimeError("ServiceMesh has no transport connected")
        return ServiceProxy(self._transport, service)


CACHE_POLICY = cache_policy(SERVICE_CLASSES)

TOOLS = collect_tools(SERVICE_CLASSES)

default_cache = InMemoryCache()


def build_local_mesh(
    db: Session,
    user_id: Optional[int],
    cache: Optional[CacheBackend] = default_cache,
) -> ServiceMesh:
    """
    Build a mesh whose services run in-process against the given DB session.

    Pass cache=None to disable caching.
    """
    mesh = ServiceMesh(user_id, tools=TOOLS)
    services = {cls.name: cls(db=db, user_id=user_id, mesh=mesh) for cls in SERVICE_CLASSES}
    transport: Transport = LocalTransport(services)
    if cache is not None:
        transport = CachingTransport(transport, cache, user_id, CACHE_POLICY)
    mesh.connect(transport)
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
