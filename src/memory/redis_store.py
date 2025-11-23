import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
import redis.asyncio as redis
from .types import ShortTermMemory, ShortTermMemoryOut, ShortTermType, ShortTermMemoryUpdate


class ShortTermStore:
    """Redis-based short term memory store"""
    
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
        
        formatted_time = now.strftime("%d-%m-%Y %H:%M")
        
        if m.memory_type == ShortTermType.CACHE:
            payload = {
                "id": id_,
                "agent_id": m.agent_id,
                "memory": m.memory,
                "memory_type": m.memory_type.value,
                "ttl": m.ttl,
                "message_id": m.message_id,
                "run_id": m.run_id,
                "created_at": now,
                "updated_at": None
            }
            redis_payload = {
                "id": id_,
                "agent_id": m.agent_id,
                "memory": m.memory,
                "memory_type": m.memory_type.value,
                "ttl": m.ttl,
                "message_id": m.message_id,
                "run_id": m.run_id,
                "created_at": formatted_time,
                "updated_at": None
            }
        else:
            payload = {
                "id": id_,
                "agent_id": m.agent_id,
                "memory": m.memory,
                "memory_type": m.memory_type.value,
                "ttl": m.ttl,
                "message_id": m.message_id,
                "run_id": m.run_id,
                "workflow_id": m.workflow_id,
                "stages": m.stages if m.stages else [],
                "current_stage": m.current_stage,
                "context_log_summary": m.context_log_summary,
                "user_query": m.user_query,
                "created_at": now,
                "updated_at": None
            }
            redis_payload = {
                "id": id_,
                "agent_id": m.agent_id,
                "memory": m.memory,
                "memory_type": m.memory_type.value,
                "ttl": m.ttl,
                "message_id": m.message_id,
                "run_id": m.run_id,
                "workflow_id": m.workflow_id,
                "stages": m.stages if m.stages else [],
                "current_stage": m.current_stage,
                "context_log_summary": m.context_log_summary,
                "user_query": m.user_query,
                "created_at": formatted_time,
                "updated_at": None
            }
       
        pipe = self.r.pipeline()
        pipe.set(key, json.dumps(redis_payload), ex=m.ttl)
        pipe.zadd(self._idx(m.memory_type, m.agent_id), {id_: now.timestamp()})
        await pipe.execute()
        return ShortTermMemoryOut(**payload)

    async def update(self, update: ShortTermMemoryUpdate) -> Optional[dict]:
        """Update short-term memory by agent_id and message_id"""
        idx = self._idx(update.memory_type, update.agent_id)
        ids = await self.r.zrevrange(idx, 0, -1)
        
        for id_ in ids:
            key = self._key(update.memory_type, update.agent_id, id_)
            raw = await self.r.get(key)
            if raw is None:
                continue
                
            data = json.loads(raw)
            
            if data.get("message_id") == update.message_id:
                now = datetime.now(timezone.utc)
                
                memory = data.get("memory", {})
                
                if update.memory_updates:
                    memory.update(update.memory_updates)
                
                for key_to_remove in update.remove_keys:
                    memory.pop(key_to_remove, None)
                
                data["memory"] = memory
                data["updated_at"] = now.strftime("%d-%m-%Y %H:%M")
                
                if update.memory_type == ShortTermType.WORKING:
                    if update.workflow_id and update.workflow_id != "":
                        data["workflow_id"] = update.workflow_id

                    if update.stages and len(update.stages) > 0:
                        data["stages"] = update.stages

                    if update.current_stage and update.current_stage != "":
                        data["current_stage"] = update.current_stage

                    if update.context_log_summary and update.context_log_summary != "":
                        data["context_log_summary"] = update.context_log_summary

                    if update.user_query and update.user_query != "":
                        data["user_query"] = update.user_query
                
                if update.ttl and update.ttl > 0 and update.ttl != 600:
                    ttl = update.ttl
                else:
                    ttl = data.get("ttl", 600)

                await self.r.set(key, json.dumps(data), ex=ttl)
                return data
        
        return None

    async def get_many(
        self, 
        mem_type: ShortTermType, 
        agent_id: str, 
        message_id: Optional[str] = None,
        run_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> List[dict]:
        """Get memories with clean schema"""
        idx = self._idx(mem_type, agent_id)
        ids = await self.r.zrevrange(idx, 0, -1)
        results: List[dict] = []
        to_prune: List[str] = []
        
        for id_ in ids:
            key = self._key(mem_type, agent_id, id_)
            raw = await self.r.get(key)
            if raw is None:
                to_prune.append(id_)
                continue
            
            data = json.loads(raw)
            
            if message_id and data.get("message_id") != message_id:
                continue
            if run_id and data.get("run_id") != run_id:
                continue
            if workflow_id and data.get("workflow_id") != workflow_id:
                continue
            
            if mem_type == ShortTermType.CACHE:
                metadata = {"created_at": data["created_at"]}
                if data.get("updated_at"):
                    metadata["updated_at"] = data["updated_at"]
                
                clean_result = {
                    "agent_id": data["agent_id"],
                    "memory": data["memory"],
                    "memory_type": "cache",
                    "ttl": data["ttl"],
                    "message_id": data["message_id"],
                    "run_id": data.get("run_id"),
                    "metadata": metadata
                }
            else:
                metadata = {"created_at": data["created_at"]}
                if data.get("updated_at"):
                    metadata["updated_at"] = data["updated_at"]
                
                clean_result = {
                    "agent_id": data["agent_id"],
                    "memory": data["memory"],
                    "memory_type": "working",
                    "ttl": data["ttl"],
                    "message_id": data["message_id"],
                    "run_id": data.get("run_id"),
                    "workflow_id": data.get("workflow_id"),
                    "stages": data.get("stages", []),
                    "current_stage": data.get("current_stage"),
                    "context_log_summary": data.get("context_log_summary"),
                    "user_query": data.get("user_query"),
                    "metadata": metadata
                }
            
            results.append(clean_result)
       
        if to_prune:
            await self.r.zrem(idx, *to_prune)
        
        return results

    async def delete_by_message_id(
        self, 
        mem_type: ShortTermType, 
        agent_id: str, 
        message_id: str
    ) -> bool:
        """Delete specific memory by message_id"""
        idx = self._idx(mem_type, agent_id)
        ids = await self.r.zrevrange(idx, 0, -1)
        
        for id_ in ids:
            key = self._key(mem_type, agent_id, id_)
            raw = await self.r.get(key)
            if raw is None:
                continue
                
            data = json.loads(raw)
            
            if data.get("message_id") == message_id:
                pipe = self.r.pipeline()
                pipe.delete(key)
                pipe.zrem(idx, id_)
                await pipe.execute()
                return True
        
        return False

    async def delete_all(self, mem_type: ShortTermType, agent_id: str) -> int:
        """Delete all memories of specific type for agent"""
        idx = self._idx(mem_type, agent_id)
        ids = await self.r.zrevrange(idx, 0, -1)
        
        if not ids:
            return 0
        
        pipe = self.r.pipeline()
        for id_ in ids:
            key = self._key(mem_type, agent_id, id_)
            pipe.delete(key)
        pipe.delete(idx)
        
        await pipe.execute()
        return len(ids)