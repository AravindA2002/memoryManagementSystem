from typing import List
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .types import (
    EpisodicConversationalCreate, EpisodicSummaryCreate, EpisodicObservationCreate,
    ProceduralAgentCreate, ProceduralToolCreate, ProceduralWorkflowCreate
)

COLS = {
    # episodic sub-tables
    "episodic_conversational": "lt_episodic_conversational",
    "episodic_summaries": "lt_episodic_summaries",
    "episodic_observations": "lt_episodic_observations",
    # procedural sub-tables
    "procedural_agent_store": "lt_procedural_agent_store",
    "procedural_tool_store": "lt_procedural_tool_store",
    "procedural_workflow_store": "lt_procedural_workflow_store",
}

class MongoLongTermStore:
    def __init__(self, mongo_url: str, db_name: str = "memory"):
        self.client = AsyncIOMotorClient(mongo_url)
        self.db: AsyncIOMotorDatabase = self.client[db_name]
        self._ready = False

    async def ensure_indexes(self) -> None:
        if self._ready:
            return
        # Episodic
        for cname in (COLS["episodic_conversational"], COLS["episodic_summaries"], COLS["episodic_observations"]):
            await self.db[cname].create_index([("agent_id",1), ("created_at",-1)])
            await self.db[cname].create_index([("agent_id",1), ("tags",1)])
        await self.db[COLS["episodic_conversational"]].create_index([("agent_id",1), ("conversation_id",1), ("created_at",1)])
        await self.db[COLS["episodic_summaries"]].create_index([("agent_id",1), ("conversation_id",1), ("span_start",1), ("span_end",1)])
        await self.db[COLS["episodic_observations"]].create_index([("agent_id",1), ("observation_id",1)])

        # Procedural
        await self.db[COLS["procedural_agent_store"]].create_index([("agent_id",1), ("name",1), ("version",-1)])
        await self.db[COLS["procedural_tool_store"]].create_index([("agent_id",1), ("name",1), ("version",-1)])
        await self.db[COLS["procedural_workflow_store"]].create_index([("agent_id",1), ("name",1), ("version",-1)])

        self._ready = True

    # --------- Append-only writers (Episodic) ---------
    async def create_ep_conversational(self, m: EpisodicConversationalCreate) -> str:
        await self.ensure_indexes()
        doc = m.model_dump()
        doc["id"] = str(uuid4())
        await self.db[COLS["episodic_conversational"]].insert_one(doc)
        return doc["id"]

    async def create_ep_summary(self, m: EpisodicSummaryCreate) -> str:
        await self.ensure_indexes()
        doc = m.model_dump()
        doc["id"] = str(uuid4())
        await self.db[COLS["episodic_summaries"]].insert_one(doc)
        return doc["id"]

    async def create_ep_observation(self, m: EpisodicObservationCreate) -> str:
        await self.ensure_indexes()
        doc = m.model_dump()
        doc["id"] = str(uuid4())
        await self.db[COLS["episodic_observations"]].insert_one(doc)
        return doc["id"]

    # No update methods exposed for episodic → append-only by interface

    # --------- Procedural writers ---------
    async def create_proc_agent(self, m: ProceduralAgentCreate) -> str:
        await self.ensure_indexes()
        doc = m.model_dump()
        doc["id"] = str(uuid4())
        await self.db[COLS["procedural_agent_store"]].insert_one(doc)
        return doc["id"]

    async def create_proc_tool(self, m: ProceduralToolCreate) -> str:
        await self.ensure_indexes()
        doc = m.model_dump()
        doc["id"] = str(uuid4())
        await self.db[COLS["procedural_tool_store"]].insert_one(doc)
        return doc["id"]

    async def create_proc_workflow(self, m: ProceduralWorkflowCreate) -> str:
        await self.ensure_indexes()
        doc = m.model_dump()
        doc["id"] = str(uuid4())
        await self.db[COLS["procedural_workflow_store"]].insert_one(doc)
        return doc["id"]
