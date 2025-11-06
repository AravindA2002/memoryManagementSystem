import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
import redis.asyncio as redis

from .types import RedisMemoryIn, RedisMemoryOut, RedisMemoryType

# Keys:
#  - rm:{type}:{agent_id}:{id} -> JSON value, set with TTL
#  - rmidx:{type}:{agent_id}   -> ZSET of (score=created_ts, member=id)

class RedisMemoryStore:
    def __init__(self, url: str):
        self.r = redis.from_url(url, decode_responses=True)

    @staticmethod
    def _key(mem_type: RedisMemoryType, agent_id: str, id_: str) -> str:
        return f"rm:{mem_type}:{agent_id}:{id_}"

    @staticmethod
    def _idx(mem_type: RedisMemoryType, agent_id: str) -> str:
        return f"rmidx:{mem_type}:{agent_id}"

    async def create(self, m: RedisMemoryIn) -> RedisMemoryOut:
        now = datetime.now(timezone.utc)
        id_ = str(uuid.uuid4())
        key = self._key(m.memory_type, m.agent_id, id_)
        payload = {
            "id": id_,
            "agent_id": m.agent_id,
            "memory_type": m.memory_type,
            "memory": m.memory,
            "ttl": m.ttl,
            "created_at": now.isoformat(),
        }
        # store value and TTL
        pipe = self.r.pipeline()
        pipe.set(key, json.dumps(payload), ex=m.ttl)
        pipe.zadd(self._idx(m.memory_type, m.agent_id), {id_: now.timestamp()})
        # Let the index entry auto-expire when the value is gone (cleanup on read)
        await pipe.execute()
        return RedisMemoryOut(**payload)

    async def get_many(self, mem_type: RedisMemoryType, agent_id: str, limit: int = 100) -> List[RedisMemoryOut]:
        idx = self._idx(mem_type, agent_id)
        ids = await self.r.zrevrange(idx, 0, limit - 1)
        results: List[RedisMemoryOut] = []
        to_prune: List[str] = []
        for id_ in ids:
            key = self._key(mem_type, agent_id, id_)
            raw = await self.r.get(key)
            if raw is None:
                to_prune.append(id_)
                continue
            data = json.loads(raw)
            results.append(RedisMemoryOut(**data))
        # prune missing ids from index
        if to_prune:
            await self.r.zrem(idx, *to_prune)
        return results

    async def delete(self, mem_type: RedisMemoryType, agent_id: str, id_: str) -> int:
        key = self._key(mem_type, agent_id, id_)
        idx = self._idx(mem_type, agent_id)
        pipe = self.r.pipeline()
        pipe.delete(key)
        pipe.zrem(idx, id_)
        res = await pipe.execute()
        # returns number of keys removed (value + idx member)
        return int(res[0]) + int(res[1])
