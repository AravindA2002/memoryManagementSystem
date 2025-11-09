from .redis_store import ShortTermStore
from .mongo_longterm import LongTermStore
from .chroma_semantic import ChromaSemanticStore
from .embeddings import openai_embed
from .neo4j_associative import Neo4jAssociativeStore
from ..config.settings import (
    REDIS_URL, MONGO_URL, MONGO_DB, CHROMA_HOST, CHROMA_PORT
)
import json
from typing import Optional, List
from datetime import datetime

from .types import (
    ShortTermMemory, ShortTermType, ShortTermMemoryUpdate,
    LongTermMemory, LongTermType, LongTermMemoryUpdate
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
        self.short_term = ShortTermStore(redis_url or REDIS_URL)
        self.long_term = LongTermStore(mongo_url or MONGO_URL, mongo_db or MONGO_DB)
        self.semantic = chroma_semantic or ChromaSemanticStore(CHROMA_HOST, CHROMA_PORT)
        self.embed = openai_embed_fn or openai_embed
        self.associative = Neo4jAssociativeStore()

    # ==================== SHORT TERM MEMORY ====================
    
    async def add_short_term(self, m: ShortTermMemory):
        """Add any short-term memory (cache or working)"""
        return await self.short_term.create(m)
    
    async def update_short_term(self, update: ShortTermMemoryUpdate):
        """Update short-term memory by agent_id and message_id"""
        return await self.short_term.update(update)
    
    async def get_short_term(
        self, 
        memory_type: ShortTermType,
        agent_id: str, 
        message_id: Optional[str] = None,
        run_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ):
        """Retrieve short-term memories from Redis"""
        return await self.short_term.get_many(memory_type, agent_id, message_id, run_id, workflow_id)

    # ==================== LONG TERM MEMORY ====================
    
    async def add_long_term(self, m: LongTermMemory) -> str:
        """Add any long-term memory (semantic, episodic, or procedural)"""
        
        # Handle semantic memory with embeddings
        if m.memory_type == LongTermType.SEMANTIC:
            text_to_embed = json.dumps(m.memory, sort_keys=True)
            normalized = m.normalized_text or text_to_embed
            
            # Store in Chroma for semantic search
            await self.semantic.add(
                agent_id=m.agent_id,
                text=text_to_embed,
                normalized_text=normalized,
                embed_fn=self.embed
            )
        
        # Store in MongoDB
        return await self.long_term.create(m)
    
    async def update_long_term(self, update: LongTermMemoryUpdate):
        """Update long-term memory by agent_id and message_id"""
        result = await self.long_term.update(update)
        
        # If semantic memory was updated, update Chroma as well
        if result and update.memory_type == LongTermType.SEMANTIC:
            # Note: ChromaDB doesn't support update, so we'd need to delete and re-add
            # For now, just update MongoDB. Consider implementing delete+add for Chroma if needed.
            pass
        
        return result
    
    async def get_long_term(
        self,
        memory_type: LongTermType,
        agent_id: str,
        subtype: Optional[str] = None,
        message_id: Optional[str] = None,
        run_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        name: Optional[str] = None
    ):
        """Retrieve long-term memories from MongoDB"""
        return await self.long_term.get_many(
            memory_type, agent_id, subtype, message_id, 
            run_id, workflow_id, conversation_id, name
        )
    
    async def search_semantic(self, agent_id: str, query: str, k: int = 10):
        """Search semantic memories using vector similarity"""
        return await self.semantic.similarity_search(agent_id, query, self.embed, k)

    # ==================== WORKING MEMORY PERSISTENCE ====================
    
    async def persist_working_memory(self, agent_id: str, workflow_id: str) -> List[str]:
        """
        Persist working memories from short-term (Redis) to long-term (MongoDB)
        """
        # Get working memories from Redis
        working_memories = await self.short_term.get_many(
            ShortTermType.WORKING, agent_id, workflow_id=workflow_id
        )
        
        persisted_ids = []
        for wm in working_memories:
            # Convert to long-term memory
            long_term_mem = LongTermMemory(
                agent_id=wm.agent_id,
                memory=wm.memory,
                memory_type=LongTermType.EPISODIC,
                subtype="working_persisted",
                message_id=wm.message_id,
                run_id=wm.run_id,
                workflow_id=wm.workflow_id,
                stages=wm.stages,
                current_stage=wm.current_stage,
                context_log_summary=wm.context_log_summary,
                user_query=wm.user_query,
                created_at=wm.created_at if isinstance(wm.created_at, datetime) else datetime.fromisoformat(wm.created_at),
                persisted_at=datetime.utcnow(),
                original_ttl=wm.ttl
            )
            
            doc_id = await self.long_term.create(long_term_mem)
            persisted_ids.append(doc_id)
        
        return persisted_ids