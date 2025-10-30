from __future__ import annotations
import os, json
from typing import List, Optional
import redis
from .models import Memory

class RedisStore:
    
    def __init__(self, url: str | None = None):
        url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r = redis.from_url(url, decode_responses=True)

    @staticmethod
    def _key(mem_id: str) -> str:
        return f"mem:{mem_id}"

    def store(self, mem: Memory, ttl_seconds: int = 3600, working_scope: Optional[str] = None):
        payload = mem.model_dump()
        self.r.set(self._key(mem.id), json.dumps(payload), ex=ttl_seconds)
        if working_scope:
            s_key = f"scope:{working_scope}"
            self.r.sadd(s_key, mem.id)
            self.r.expire(s_key, ttl_seconds)

    def fetch_all(self, subset_ids: Optional[List[str]] = None) -> List[Memory]:
        ids = subset_ids or [k.split("mem:")[1] for k in self.r.keys("mem:*")]
        if not ids:
            return []
        pipe = self.r.pipeline()
        for i in ids:
            pipe.get(self._key(i))
        rows = pipe.execute()
        out: List[Memory] = []
        for blob in rows:
            if blob:
                try:
                    out.append(Memory(**json.loads(blob)))
                except Exception:
                    pass
        return out

    def scope_ids(self, scope: str) -> List[str]:
        return list(self.r.smembers(f"scope:{scope}"))
