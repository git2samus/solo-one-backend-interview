import copy
import threading
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, FrozenSet, Hashable, Iterable, Optional, Set, Tuple

CACHE_READS_ATTR = "__cache_reads__"

CacheEntry = Tuple[Any, FrozenSet[str]]


def cached(func: Optional[Callable] = None, *, reads: Iterable[str] = ()):
    """
    Mark a service method as a cacheable read.

    reads names other services whose data the method reads directly from the
    database. Calls made through the mesh are tracked automatically and don't
    need to be listed.
    """

    def mark(f: Callable) -> Callable:
        setattr(f, CACHE_READS_ATTR, frozenset(reads))
        return f

    return mark(func) if func is not None else mark


def cache_policy(service_classes: Iterable[type]) -> Dict[Tuple[str, str], FrozenSet[str]]:
    """
    Map (service, method) for every @cached method to the services it reads.
    """
    policy = {}
    for cls in service_classes:
        for attr in dir(cls):
            reads = getattr(getattr(cls, attr), CACHE_READS_ATTR, None)
            if reads is not None:
                policy[(cls.name, attr)] = reads | {cls.name}
    return policy


class CacheBackend(ABC):
    """
    Storage for cached service results.

    Entries are tagged with the services whose data they read, so a write to
    a service can invalidate every entry depending on it. version() changes on
    every invalidation; set() discards results computed before the latest
    invalidation, so a read racing a write can't store stale data.
    """

    @abstractmethod
    def get(self, key: Hashable) -> Optional[CacheEntry]:
        ...

    @abstractmethod
    def set(self, key: Hashable, value: Any, tags: FrozenSet[str], version: int) -> None:
        ...

    @abstractmethod
    def invalidate(self, tags: Iterable[str]) -> None:
        ...

    @abstractmethod
    def version(self) -> int:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...


class InMemoryCache(CacheBackend):
    """
    Process-local cache backend for local development.

    Values are deep-copied in and out so callers can't mutate cached results.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._entries: Dict[Hashable, CacheEntry] = {}
        self._keys_by_tag: Dict[str, Set[Hashable]] = {}
        self._version = 0

    def get(self, key: Hashable) -> Optional[CacheEntry]:
        with self._lock:
            entry = self._entries.get(key)
        if entry is None:
            return None
        value, tags = entry
        return copy.deepcopy(value), tags

    def set(self, key: Hashable, value: Any, tags: FrozenSet[str], version: int) -> None:
        with self._lock:
            if version != self._version:
                return
            self._entries[key] = (copy.deepcopy(value), tags)
            for tag in tags:
                self._keys_by_tag.setdefault(tag, set()).add(key)

    def invalidate(self, tags: Iterable[str]) -> None:
        with self._lock:
            self._version += 1
            for tag in tags:
                for key in self._keys_by_tag.pop(tag, ()):
                    self._entries.pop(key, None)

    def version(self) -> int:
        with self._lock:
            return self._version

    def clear(self) -> None:
        with self._lock:
            self._version += 1
            self._entries.clear()
            self._keys_by_tag.clear()
