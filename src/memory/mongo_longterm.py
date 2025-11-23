from typing import List, Optional, Union
from uuid import uuid4
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .types import (
    LongTermType,
    SemanticMemoryStorage, ConversationalMemoryStorage, SummariesMemoryStorage,
    ObservationsMemoryStorage, ProceduralMemoryStorage,
    WorkingMemoryPersisted, WorkingMemoryPersistedUpdate,
    LongTermMemoryUpdateStorage
)

COLS = {
    "semantic": "lt_semantic",
    "episodic": "lt_episodic",
    "procedural": "lt_procedural",
    "working_persisted": "lt_working_persisted",
}

class LongTermStore:
    """MongoDB-based long term memory store"""
    
    def __init__(self, mongo_url: str, db_name: str = "memory"):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db: AsyncIOMotorDatabase = self.client[db_name]
        self._ready = False

    async def ensure_indexes(self) -> None:
        if self._ready:
            return
       
        for col_name in COLS.values():
            await self.db[col_name].create_index([("agent_id", 1), ("created_at", -1)])
            await self.db[col_name].create_index([("agent_id", 1), ("message_id", 1)])
            await self.db[col_name].create_index([("agent_id", 1), ("run_id", 1)])
            await self.db[col_name].create_index([("agent_id", 1), ("tags", 1)])
        
        await self.db[COLS["episodic"]].create_index([("agent_id", 1), ("subtype", 1)])
        await self.db[COLS["episodic"]].create_index([("agent_id", 1), ("conversation_id", 1)])
        
        await self.db[COLS["procedural"]].create_index([("agent_id", 1), ("name", 1), ("version", -1)])
        await self.db[COLS["procedural"]].create_index([("agent_id", 1), ("subtype", 1)])
        
        await self.db[COLS["working_persisted"]].create_index([("agent_id", 1), ("workflow_id", 1)])
        await self.db[COLS["working_persisted"]].create_index([("workflow_id", 1)])
        await self.db[COLS["working_persisted"]].create_index([("agent_id", 1), ("persisted_at", -1)])

        self._ready = True

    async def create(
    self, 
    m: Union[
        SemanticMemoryStorage,
        ConversationalMemoryStorage,
        SummariesMemoryStorage,
        ObservationsMemoryStorage,
        ProceduralMemoryStorage
    ]
) -> str:
        """Create long-term memory entry with clean schema"""
        await self.ensure_indexes()
        doc = m.model_dump()  # Remove exclude_none=True to store all fields including None
        doc["id"] = str(uuid4())
        
        collection = COLS[m.memory_type.value if hasattr(m.memory_type, 'value') else m.memory_type]
        await self.db[collection].insert_one(doc)
        return doc["id"]


    
    async def create_working_persisted(self, m: WorkingMemoryPersisted) -> str:
        """Create working_persisted memory"""
        await self.ensure_indexes()
        doc = m.model_dump(exclude_none=True)  # Only include non-None fields
        doc["id"] = str(uuid4())
        
        collection = COLS["working_persisted"]
        await self.db[collection].insert_one(doc)
        return doc["id"]

    async def update(self, update: LongTermMemoryUpdateStorage) -> Optional[dict]:
        """Update long-term memory by agent_id and message_id"""
        await self.ensure_indexes()
        
        collection = COLS[update.memory_type.value]
        
        query = {
            "agent_id": update.agent_id,
            "message_id": update.message_id
        }
        
        existing = await self.db[collection].find_one(query, {"_id": 0})
        
        if not existing:
            return None
        
        update_ops = {}
        
        if update.memory_updates:
            for key, value in update.memory_updates.items():
                update_ops[f"memory.{key}"] = value
        
        unset_ops = {}
        for key in update.remove_keys:
            unset_ops[f"memory.{key}"] = ""
        
        if update.normalized_text is not None:
            update_ops["normalized_text"] = update.normalized_text
        if update.subtype is not None:
            update_ops["subtype"] = update.subtype
        if update.conversation_id is not None:
            update_ops["conversation_id"] = update.conversation_id
        if update.name is not None:
            update_ops["name"] = update.name
        if update.status is not None:
            update_ops["status"] = update.status
        
        if update.config_updates:
            for key, value in update.config_updates.items():
                update_ops[f"config.{key}"] = value
        
        update_ops["version"] = existing.get("version", 1) + 1
        update_ops["updated_at"] = datetime.utcnow()
        
        mongo_update = {}
        if update_ops:
            mongo_update["$set"] = update_ops
        if unset_ops:
            mongo_update["$unset"] = unset_ops
        
        if mongo_update:
            await self.db[collection].update_one(query, mongo_update)
        
        updated = await self.db[collection].find_one(query, {"_id": 0})
        return updated

    async def update_working_persisted(self, update: WorkingMemoryPersistedUpdate) -> Optional[dict]:
        """Update working_persisted memory"""
        await self.ensure_indexes()
        
        collection = COLS["working_persisted"]
        
        query = {
            "agent_id": update.agent_id,
            "message_id": update.message_id
        }
        
        existing = await self.db[collection].find_one(query, {"_id": 0})
        
        if not existing:
            return None
        
        update_ops = {}
        
        if update.memory_updates:
            for key, value in update.memory_updates.items():
                update_ops[f"memory.{key}"] = value
        
        unset_ops = {}
        for key in update.remove_keys:
            unset_ops[f"memory.{key}"] = ""
        
        if update.workflow_id is not None:
            update_ops["workflow_id"] = update.workflow_id
        if update.stages is not None:
            update_ops["stages"] = update.stages
        if update.current_stage is not None:
            update_ops["current_stage"] = update.current_stage
        if update.context_log_summary is not None:
            update_ops["context_log_summary"] = update.context_log_summary
        if update.user_query is not None:
            update_ops["user_query"] = update.user_query
        if update.tags is not None:
            update_ops["tags"] = update.tags
        
        update_ops["version"] = existing.get("version", 1) + 1
        update_ops["updated_at"] = datetime.utcnow()
        
        mongo_update = {}
        if update_ops:
            mongo_update["$set"] = update_ops
        if unset_ops:
            mongo_update["$unset"] = unset_ops
        
        if mongo_update:
            await self.db[collection].update_one(query, mongo_update)
        
        updated = await self.db[collection].find_one(query, {"_id": 0})
        return updated

    async def get_many(
        self,
        memory_type: LongTermType,
        agent_id: str,
        subtype: Optional[str] = None,
        message_id: Optional[str] = None,
        run_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> List[dict]:
        """Retrieve long-term memories"""
        await self.ensure_indexes()
        
        query = {"agent_id": agent_id}
        if subtype:
            query["subtype"] = subtype
        if message_id:
            query["message_id"] = message_id
        if run_id:
            query["run_id"] = run_id
        if workflow_id:
            query["workflow_id"] = workflow_id
        if conversation_id:
            query["conversation_id"] = conversation_id
        if name:
            query["name"] = name
            
        collection = COLS[memory_type.value]
        cur = (
            self.db[collection]
            .find(query, {"_id": 0})
            .sort("created_at", -1)
        )
        return await cur.to_list(length=None)
    
    async def get_working_persisted(
        self,
        agent_id: str,
        workflow_id: Optional[str] = None,
        message_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> List[dict]:
        """Retrieve working_persisted memories"""
        await self.ensure_indexes()
        
        query = {"agent_id": agent_id}
        if workflow_id:
            query["workflow_id"] = workflow_id
        if message_id:
            query["message_id"] = message_id
        if run_id:
            query["run_id"] = run_id
            
        collection = COLS["working_persisted"]
        cur = (
            self.db[collection]
            .find(query, {"_id": 0})
            .sort("persisted_at", -1)
        )
        return await cur.to_list(length=None)

    async def delete_by_message_id(
        self,
        memory_type: LongTermType,
        agent_id: str,
        message_id: str
    ) -> bool:
        """Delete specific memory by message_id"""
        await self.ensure_indexes()
        
        collection = COLS[memory_type.value]
        query = {
            "agent_id": agent_id,
            "message_id": message_id
        }
        
        result = await self.db[collection].delete_one(query)
        return result.deleted_count > 0
    
    async def delete_working_persisted_by_message_id(
        self,
        agent_id: str,
        message_id: str
    ) -> bool:
        """Delete specific working_persisted memory"""
        await self.ensure_indexes()
        
        collection = COLS["working_persisted"]
        query = {
            "agent_id": agent_id,
            "message_id": message_id
        }
        
        result = await self.db[collection].delete_one(query)
        return result.deleted_count > 0

    async def delete_all(
        self,
        memory_type: LongTermType,
        agent_id: str
    ) -> int:
        """Delete all memories of specific type"""
        await self.ensure_indexes()
        
        collection = COLS[memory_type.value]
        query = {"agent_id": agent_id}
        
        result = await self.db[collection].delete_many(query)
        return result.deleted_count
    
    async def delete_all_working_persisted(
        self,
        agent_id: str
    ) -> int:
        """Delete all working_persisted memories"""
        await self.ensure_indexes()
        
        collection = COLS["working_persisted"]
        query = {"agent_id": agent_id}
        
        result = await self.db[collection].delete_many(query)
        return result.deleted_count