from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .types import LongTermMemory, LongTermType, LongTermMemoryUpdate

COLS = {
    "semantic": "lt_semantic",
    "episodic": "lt_episodic",
    "procedural": "lt_procedural",
}

class LongTermStore:
    """MongoDB-based Long Term Memory Store (Semantic, Episodic, Procedural)"""
    
    def __init__(self, mongo_url: str, db_name: str = "memory"):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db: AsyncIOMotorDatabase = self.client[db_name]
        self._ready = False

    async def ensure_indexes(self) -> None:
        if self._ready:
            return
       
        # Common indexes for all long-term memory types
        for col_name in COLS.values():
            await self.db[col_name].create_index([("agent_id", 1), ("created_at", -1)])
            await self.db[col_name].create_index([("agent_id", 1), ("message_id", 1)])
            await self.db[col_name].create_index([("agent_id", 1), ("run_id", 1)])
            await self.db[col_name].create_index([("agent_id", 1), ("tags", 1)])
        
        # Episodic specific indexes
        await self.db[COLS["episodic"]].create_index([("agent_id", 1), ("subtype", 1)])
        await self.db[COLS["episodic"]].create_index([("agent_id", 1), ("conversation_id", 1)])
        await self.db[COLS["episodic"]].create_index([("agent_id", 1), ("workflow_id", 1)])
        await self.db[COLS["episodic"]].create_index([("workflow_id", 1)])
        
        # Procedural specific indexes
        await self.db[COLS["procedural"]].create_index([("agent_id", 1), ("name", 1), ("version", -1)])
        await self.db[COLS["procedural"]].create_index([("agent_id", 1), ("subtype", 1)])

        self._ready = True

    async def create(self, m: LongTermMemory) -> str:
        """Create a long-term memory entry"""
        await self.ensure_indexes()
        doc = m.model_dump()
        doc["id"] = str(uuid4())
        
        # Store in appropriate collection based on memory_type
        collection = COLS[m.memory_type.value]
        await self.db[collection].insert_one(doc)
        return doc["id"]

    async def update(self, update: LongTermMemoryUpdate) -> Optional[dict]:
        """Update a long-term memory by agent_id and message_id"""
        await self.ensure_indexes()
        
        collection = COLS[update.memory_type.value]
        
        # Find the document
        query = {
            "agent_id": update.agent_id,
            "message_id": update.message_id
        }
        
        existing = await self.db[collection].find_one(query, {"_id": 0})
        
        if not existing:
            return None
        
        # Prepare update operations
        update_ops = {}
        
        # Update memory dictionary
        if update.memory_updates:
            for key, value in update.memory_updates.items():
                update_ops[f"memory.{key}"] = value
        
        # Remove keys from memory
        unset_ops = {}
        for key in update.remove_keys:
            unset_ops[f"memory.{key}"] = ""
        
        # Update metadata
        if update.metadata_updates:
            for key, value in update.metadata_updates.items():
                update_ops[f"metadata.{key}"] = value
        
        # Update other fields
        if update.tags is not None:
            update_ops["tags"] = update.tags
        if update.normalized_text is not None:
            update_ops["normalized_text"] = update.normalized_text
        if update.subtype is not None:
            update_ops["subtype"] = update.subtype
        if update.conversation_id is not None:
            update_ops["conversation_id"] = update.conversation_id
        if update.workflow_id is not None:
            update_ops["workflow_id"] = update.workflow_id
        if update.name is not None:
            update_ops["name"] = update.name
        if update.status is not None:
            update_ops["status"] = update.status
        
        # Update config for procedural
        if update.config_updates:
            for key, value in update.config_updates.items():
                update_ops[f"config.{key}"] = value
        
        # Increment version
        update_ops["version"] = existing.get("version", 1) + 1
        update_ops["updated_at"] = datetime.utcnow()
        
        # Perform update
        mongo_update = {}
        if update_ops:
            mongo_update["$set"] = update_ops
        if unset_ops:
            mongo_update["$unset"] = unset_ops
        
        if mongo_update:
            await self.db[collection].update_one(query, mongo_update)
        
        # Return updated document
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
        """Retrieve long-term memories with filters"""
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

    async def delete_by_message_id(
        self,
        memory_type: LongTermType,
        agent_id: str,
        message_id: str
    ) -> bool:
        """Delete a specific memory by message_id"""
        await self.ensure_indexes()
        
        collection = COLS[memory_type.value]
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
        """Delete all memories of a specific type for an agent"""
        await self.ensure_indexes()
        
        collection = COLS[memory_type.value]
        query = {"agent_id": agent_id}
        
        result = await self.db[collection].delete_many(query)
        return result.deleted_count
    
    