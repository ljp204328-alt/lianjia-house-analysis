import time
import threading


class TTLCache:
    """线程安全的简易 TTL 缓存，替代原先散落的 *_CACHE 字典"""

    def __init__(self, ttl=300):
        self.ttl = ttl
        self._store = {}
        self._lock = threading.Lock()

    def get(self, key, default=None):
        """命中且未过期返回缓存值，否则返回 default"""
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return default
            value, ts = item
            if time.time() - ts >= self.ttl:
                self._store.pop(key, None)
                return default
            return value

    def set(self, key, value):
        with self._lock:
            self._store[key] = (value, time.time())

    def clear(self):
        with self._lock:
            self._store.clear()


# 各接口独立缓存实例（保持与原 Django 版一致的隔离性）
CACHE = TTLCache(ttl=300)
