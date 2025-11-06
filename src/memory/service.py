# src/memory/service.py
from .redis_store import RedisMemoryStore
from .mongo_longterm import MongoLongTermStore
from .chroma_semantic import ChromaSemanticStore
from .embeddings import openai_embed
from ..config.settings import REDIS_URL, MONGO_URL, MONGO_DB, CHROMA_HOST, CHROMA_PORT
import os
from .chroma_semantic import ChromaSemanticStore
from .neo4j_associative import Neo4jAssociativeStore

from .types import (
    RedisMemoryIn, SemanticCreate,
    EpisodicConversationalCreate, EpisodicSummaryCreate, EpisodicObservationCreate,
    ProceduralAgentCreate, ProceduralToolCreate, ProceduralWorkflowCreate,
)

class MemoryService:
    def __init__(
        self,
        redis_url: str | None = None,
        mongo_url: str | None = None,
        mongo_db: str | None = None,
        chroma_semantic: ChromaSemanticStore | None = None,
        openai_embed_fn=None,
    ):
        # use env-driven defaults if not provided
        self.redis = RedisMemoryStore(redis_url or REDIS_URL)
        self.mongo = MongoLongTermStore(mongo_url or MONGO_URL, (mongo_db or MONGO_DB))
        self.semantic = chroma_semantic or ChromaSemanticStore(CHROMA_HOST, CHROMA_PORT)
        self.embed = openai_embed_fn or openai_embed
        self.associative = Neo4jAssociativeStore()

    # -------- Redis short-lived --------
    async def add_short_term(self, m: RedisMemoryIn):
        assert m.memory_type == "short_term"
        return await self.redis.create(m)

    async def add_working(self, m: RedisMemoryIn):
        assert m.memory_type == "working"
        return await self.redis.create(m)

    # -------- Semantic (Chroma) --------
    async def add_semantic(self, m: SemanticCreate) -> str:
        return await self.semantic.add(
            agent_id=m.agent_id,
            text=m.memory,
            normalized_text=m.normalized_text or m.memory,
            embed_fn=self.embed
        )

    async def search_semantic(self, agent_id: str, query: str, k: int = 10):
        return await self.semantic.similarity_search(agent_id, query, self.embed, k)

    # -------- Episodic (append-only) --------
    async def add_ep_conversational(self, m: EpisodicConversationalCreate) -> str:
        return await self.mongo.create_ep_conversational(m)

    async def add_ep_summary(self, m: EpisodicSummaryCreate) -> str:
        return await self.mongo.create_ep_summary(m)

    async def add_ep_observation(self, m: EpisodicObservationCreate) -> str:
        return await self.mongo.create_ep_observation(m)

    # -------- Procedural --------
    async def add_proc_agent(self, m: ProceduralAgentCreate) -> str:
        return await self.mongo.create_proc_agent(m)

    async def add_proc_tool(self, m: ProceduralToolCreate) -> str:
        return await self.mongo.create_proc_tool(m)

    async def add_proc_workflow(self, m: ProceduralWorkflowCreate) -> str:
        return await self.mongo.create_proc_workflow(m)
