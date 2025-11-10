from .redis_store import ShortTermStore
from .mongo_longterm import LongTermStore
from .chroma_semantic import ChromaSemanticStore
from .embeddings import openai_embed
from .neo4j_associative import Neo4jAssociativeStore
from ..config.settings import (
    REDIS_URL, MONGO_URL, MONGO_DB, CHROMA_HOST, CHROMA_PORT
)
import json
import uuid
from typing import Optional, List, Dict, Any
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

    @staticmethod
    def _generate_message_id() -> str:
        """Generate a unique message ID with timestamp prefix for better sorting"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]  # Short UUID
        return f"msg_{timestamp}_{unique_id}"

    # ==================== SHORT TERM MEMORY ====================
    
    async def add_short_term(self, m: ShortTermMemory) -> Dict[str, Any]:
        """Add any short-term memory (cache or working)"""
        # Auto-generate message_id
        message_id = self._generate_message_id()
        m.message_id = message_id
        
        result = await self.short_term.create(m)
        
        # Return message_id for user to use in retrieval/update
        return {
            "message_id": message_id,
            "agent_id": m.agent_id,
            "memory_type": m.memory_type.value,
            "created_at": result.created_at.isoformat(),
            "ttl": m.ttl
        }
    
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

    async def delete_short_term(
        self,
        memory_type: ShortTermType,
        agent_id: str,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete short-term memory - specific message_id or all (flush)"""
        if message_id:
            # Delete specific memory
            deleted = await self.short_term.delete_by_message_id(memory_type, agent_id, message_id)
            return {
                "status": "deleted" if deleted else "not_found",
                "agent_id": agent_id,
                "memory_type": memory_type.value,
                "message_id": message_id,
                "deleted_count": 1 if deleted else 0
            }
        else:
            # Flush all memories of this type for this agent
            count = await self.short_term.delete_all(memory_type, agent_id)
            return {
                "status": "flushed",
                "agent_id": agent_id,
                "memory_type": memory_type.value,
                "deleted_count": count
            }

    # ==================== LONG TERM MEMORY ====================
    
    async def add_long_term(self, m: LongTermMemory) -> Dict[str, Any]:
        """Add any long-term memory (semantic, episodic, or procedural)"""
        
        # Auto-generate message_id
        message_id = self._generate_message_id()
        m.message_id = message_id
        
        # Handle semantic memory with embeddings
        if m.memory_type == LongTermType.SEMANTIC:
            text_to_embed = json.dumps(m.memory, sort_keys=True)
            normalized = m.normalized_text or text_to_embed
            
            # Store in Chroma for semantic search
            await self.semantic.add(
                agent_id=m.agent_id,
                text=text_to_embed,
                normalized_text=normalized,
                embed_fn=self.embed,
                message_id=message_id
            )
        
        # Store in MongoDB
        await self.long_term.create(m)
        
        # Return message_id for user to use in retrieval/update
        return {
            "message_id": message_id,
            "agent_id": m.agent_id,
            "memory_type": m.memory_type.value,
            "subtype": m.subtype,
            "created_at": m.created_at.isoformat()
        }
    
    async def update_long_term(self, update: LongTermMemoryUpdate):
        """Update long-term memory by agent_id and message_id"""
        # Update in MongoDB first
        result = await self.long_term.update(update)
        
        if not result:
            return None
        
        # If semantic memory was updated, update Chroma as well (delete + re-add)
        if update.memory_type == LongTermType.SEMANTIC:
            # Reconstruct the text from updated memory
            text_to_embed = json.dumps(result.get("memory", {}), sort_keys=True)
            normalized = result.get("normalized_text") or text_to_embed
            
            # Update in Chroma (delete and re-add)
            await self.semantic.update(
                agent_id=update.agent_id,
                message_id=update.message_id,
                text=text_to_embed,
                normalized_text=normalized,
                embed_fn=self.embed
            )
        
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
    
    async def delete_long_term(
        self,
        memory_type: LongTermType,
        agent_id: str,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete long-term memory - specific message_id or all of a type"""
        if message_id:
            # Delete specific memory
            deleted = await self.long_term.delete_by_message_id(memory_type, agent_id, message_id)
            
            # Also delete from Chroma if semantic
            if deleted and memory_type == LongTermType.SEMANTIC:
                await self.semantic.delete_by_message_id(agent_id, message_id)
            
            return {
                "status": "deleted" if deleted else "not_found",
                "agent_id": agent_id,
                "memory_type": memory_type.value,
                "message_id": message_id,
                "deleted_count": 1 if deleted else 0
            }
        else:
            # Delete all memories of this type for this agent
            count = await self.long_term.delete_all(memory_type, agent_id)
            
            # Also delete from Chroma if semantic
            if memory_type == LongTermType.SEMANTIC:
                await self.semantic.delete_all(agent_id)
            
            return {
                "status": "deleted_all",
                "agent_id": agent_id,
                "memory_type": memory_type.value,
                "deleted_count": count
            }
    
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
            
            # Use the existing message_id from working memory
            long_term_mem.message_id = wm.message_id
            
            doc_id = await self.long_term.create(long_term_mem)
            persisted_ids.append(wm.message_id)  # Return message_id instead of doc_id
        
        return persisted_ids