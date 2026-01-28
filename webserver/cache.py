import shutil
import time

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CacheEntry:
    path: Path
    last_access: float = field(default_factory=time.time)


class FileCache:
    def __init__(
        self, cache_dir: Path, max_entries: int = 10, max_age_seconds: int = 3600
    ):
        self.cache_dir = cache_dir
        self.max_entries = max_entries
        self.max_age_seconds = max_age_seconds
        self._entries: dict[str, CacheEntry] = {}
        self._cleanup_stale()

    def _cleanup_stale(self):
        if not self.cache_dir.exists():
            return

        for item in self.cache_dir.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except OSError:
                pass

    def _evict_expired(self):
        now = time.time()
        expired = [
            key
            for key, entry in self._entries.items()
            if now - entry.last_access > self.max_age_seconds
        ]
        for key in expired:
            self._remove_entry(key)

    def _evict_oldest(self):
        while len(self._entries) >= self.max_entries:
            oldest_key = min(
                self._entries.keys(), key=lambda k: self._entries[k].last_access
            )
            self._remove_entry(oldest_key)

    def _remove_entry(self, key: str):
        entry = self._entries.pop(key, None)
        if entry and entry.path.exists():
            try:
                if entry.path.is_dir():
                    shutil.rmtree(entry.path)
                else:
                    entry.path.unlink()
            except OSError:
                pass

    def get(self, key: str) -> Path | None:
        entry = self._entries.get(key)
        if entry is None:
            return None

        if not entry.path.exists():
            del self._entries[key]
            return None

        entry.last_access = time.time()
        return entry.path

    def put(self, key: str, path: Path):
        self._evict_expired()
        self._evict_oldest()
        self._entries[key] = CacheEntry(path=path)
