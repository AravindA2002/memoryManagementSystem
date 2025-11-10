import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
import redis.asyncio as redis

from .types import ShortTermMemory, ShortTermMemoryOut, ShortTermType, ShortTermMemoryUpdate


class ShortTermStore:
    """Redis-based Short Term Memory Store (Cache + Working Memory)"""
    
    def __init__(self, url: str):
        self.r = redis.from_url(url, decode_responses=True)

    @staticmethod
    def _key(mem_type: ShortTermType, agent_id: str, id_: str) -> str:
        return f"stm:{mem_type.value}:{agent_id}:{id_}"

    @staticmethod
    def _idx(mem_type: ShortTermType, agent_id: str) -> str:
        return f"stmidx:{mem_type.value}:{agent_id}"

    async def create(self, m: ShortTermMemory) -> ShortTermMemoryOut:
        now = datetime.now(timezone.utc)
        id_ = str(uuid.uuid4())
        key = self._key(m.memory_type, m.agent_id, id_)
        
        payload = m.model_dump()
        payload.update({
            "id": id_,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        })
       
        pipe = self.r.pipeline()
        pipe.set(key, json.dumps(payload), ex=m.ttl)
        pipe.zadd(self._idx(m.memory_type, m.agent_id), {id_: now.timestamp()})
       
        await pipe.execute()
        return ShortTermMemoryOut(**payload)

    async def update(self, update: ShortTermMemoryUpdate) -> Optional[ShortTermMemoryOut]:
        """Update a short-term memory by agent_id and message_id"""
        # Find the memory by agent_id and message_id
        idx = self._idx(update.memory_type, update.agent_id)
        ids = await self.r.zrevrange(idx, 0, -1)
        
        for id_ in ids:
            key = self._key(update.memory_type, update.agent_id, id_)
            raw = await self.r.get(key)
            if raw is None:
                continue
                
            data = json.loads(raw)
            
            # Check if this is the memory we want to update
            if data.get("message_id") == update.message_id:
                now = datetime.now(timezone.utc)
                
                # Update memory dictionary
                memory = data.get("memory", {})
                
                # Apply updates
                if update.memory_updates:
                    memory.update(update.memory_updates)
                
                # Remove keys
                for key_to_remove in update.remove_keys:
                    memory.pop(key_to_remove, None)
                
                data["memory"] = memory
                data["updated_at"] = now.isoformat()
                
                # Update other fields if provided
                if update.workflow_id is not None:
                    data["workflow_id"] = update.workflow_id
                if update.stages is not None:
                    data["stages"] = update.stages
                if update.current_stage is not None:
                    data["current_stage"] = update.current_stage
                if update.context_log_summary is not None:
                    data["context_log_summary"] = update.context_log_summary
                if update.user_query is not None:
                    data["user_query"] = update.user_query
                
                # Determine TTL
                ttl = update.ttl if update.ttl is not None else data.get("ttl", 600)
                
                # Save back to Redis with updated TTL
                await self.r.set(key, json.dumps(data), ex=ttl)
                
                return ShortTermMemoryOut(**data)
        
        return None

    async def get_many(
        self, 
        mem_type: ShortTermType, 
        agent_id: str, 
        message_id: Optional[str] = None,
        run_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> List[ShortTermMemoryOut]:
        idx = self._idx(mem_type, agent_id)
        ids = await self.r.zrevrange(idx, 0, -1)  # Get all items
        results: List[ShortTermMemoryOut] = []
        to_prune: List[str] = []
        
        for id_ in ids:
            key = self._key(mem_type, agent_id, id_)
            raw = await self.r.get(key)
            if raw is None:
                to_prune.append(id_)
                continue
            data = json.loads(raw)
            
            # Apply filters
            if message_id and data.get("message_id") != message_id:
                continue
            if run_id and data.get("run_id") != run_id:
                continue
            if workflow_id and data.get("workflow_id") != workflow_id:
                continue
                
            results.append(ShortTermMemoryOut(**data))
       
        if to_prune:
            await self.r.zrem(idx, *to_prune)
        return results

    async def delete_by_message_id(
        self, 
        mem_type: ShortTermType, 
        agent_id: str, 
        message_id: str
    ) -> bool:
        """Delete a specific memory by message_id"""
        idx = self._idx(mem_type, agent_id)
        ids = await self.r.zrevrange(idx, 0, -1)
        
        for id_ in ids:
            key = self._key(mem_type, agent_id, id_)
            raw = await self.r.get(key)
            if raw is None:
                continue
                
            data = json.loads(raw)
            
            # Check if this is the memory we want to delete
            if data.get("message_id") == message_id:
                pipe = self.r.pipeline()
                pipe.delete(key)
                pipe.zrem(idx, id_)
                await pipe.execute()
                return True
        
        return False

    async def delete_all(self, mem_type: ShortTermType, agent_id: str) -> int:
        """Delete all memories of a specific type for an agent (flush cache)"""
        idx = self._idx(mem_type, agent_id)
        ids = await self.r.zrevrange(idx, 0, -1)
        
        if not ids:
            return 0
        
        # Delete all keys and the index
        pipe = self.r.pipeline()
        for id_ in ids:
            key = self._key(mem_type, agent_id, id_)
            pipe.delete(key)
        pipe.delete(idx)
        
        await pipe.execute()
        return len(ids)