from .redis_store import ShortTermStore
from .mongo_longterm import LongTermStore
from .chroma_semantic import ChromaSemanticStore
from .embeddings import openai_embed
from .neo4j_associative import Neo4jAssociativeStore
from .associative_wrapper import AssociativeMemoryWrapper
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
        
        try:
            self.associative = Neo4jAssociativeStore()
            self.associative_wrapper = AssociativeMemoryWrapper(self.associative)
            print("✅ Neo4j and Associative Wrapper initialized successfully")
        except Exception as e:
            print(f"⚠️ Neo4j connection failed: {e}")
            print("⚠️ Associative memory features will not work")
            self.associative = None
            self.associative_wrapper = None

    @staticmethod
    def _generate_message_id() -> str:
        """Generate a unique message ID with timestamp prefix (format: ddmmyyyyHHmm)"""
        timestamp = datetime.utcnow().strftime("%d%m%Y%H%M")  # ddmmyyyyHHmm
        unique_id = str(uuid.uuid4())[:8]
        return f"msg_{timestamp}_{unique_id}"

    # ==================== SHORT TERM MEMORY ====================
    
    async def add_short_term(self, m: ShortTermMemory) -> Dict[str, Any]:
        """Add any short-term memory (cache or working)"""
        message_id = self._generate_message_id()
        m.message_id = message_id
        
        result = await self.short_term.create(m)
        
        # Format created_at for response
        created_at_str = result.created_at.strftime("%d-%m-%Y %H:%M")
        
        return {
            "message_id": message_id,
            "agent_id": m.agent_id,
            "memory_type": m.memory_type.value,
            "created_at": created_at_str,  # ← Formatted string
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
            deleted = await self.short_term.delete_by_message_id(memory_type, agent_id, message_id)
            return {
                "status": "deleted" if deleted else "not_found",
                "agent_id": agent_id,
                "memory_type": memory_type.value,
                "message_id": message_id,
                "deleted_count": 1 if deleted else 0
            }
        else:
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
        
        message_id = self._generate_message_id()
        m.message_id = message_id
        
        # Handle semantic memory - ChromaDB only + auto-trigger associative wrapper
        if m.memory_type == LongTermType.SEMANTIC:
            text_to_embed = json.dumps(m.memory, sort_keys=True)
            normalized = m.normalized_text or text_to_embed
            
            # Step 1: Store in ChromaDB for vector search
            await self.semantic.add(
                agent_id=m.agent_id,
                text=text_to_embed,
                normalized_text=normalized,
                embed_fn=self.embed,
                message_id=message_id
            )
            
            # Step 2: AUTO-TRIGGER ASSOCIATIVE WRAPPER
            associative_result = None
            if self.associative_wrapper:
                try:
                    print(f"🤖 Auto-triggering associative wrapper for message_id: {message_id}")
                    
                    # Extract text from memory object
                    if isinstance(m.memory, dict) and "text" in m.memory:
                        memory_text = m.memory["text"]
                    else:
                        memory_text = json.dumps(m.memory, indent=2)
                    
                    print(f"📝 Text to analyze: {memory_text}")
                    
                    # Process text (SYNC call, no await)
                    associative_result = self.associative_wrapper.process_text(
                        text=memory_text,
                        agent_id=m.agent_id
                    )
                    
                    print(f"✅ Wrapper completed: {associative_result.get('entity_count', 0)} entities, {associative_result.get('relationship_count', 0)} relationships")
                    
                except Exception as e:
                    print(f"⚠️ Associative wrapper failed: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    associative_result = {
                        "status": "error",
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "entity_count": 0,
                        "relationship_count": 0
                    }
            
            # Return response
            response = {
                "message_id": message_id,
                "agent_id": m.agent_id,
                "memory_type": m.memory_type.value,
                "subtype": m.subtype,
                "created_at": datetime.utcnow().strftime("%d-%m-%Y %H:%M"),
                "storage": "chromadb_only"
            }
            
            # Add associative results
            if associative_result:
                response["associative"] = {
                    "status": associative_result.get("status", "error"),
                    "entities_created": associative_result.get("entity_count", 0),
                    "relationships_created": associative_result.get("relationship_count", 0)
                }
                if associative_result.get("error"):
                    response["associative"]["error"] = associative_result["error"]
            
            return response
        
        # For episodic and procedural - store in MongoDB only
        await self.long_term.create(m)
        
        return {
            "message_id": message_id,
            "agent_id": m.agent_id,
            "memory_type": m.memory_type.value,
            "subtype": m.subtype,
            "created_at": m.created_at.strftime("%d-%m-%Y %H:%M"),
            "storage": "mongodb"
        }
    
    async def update_long_term(self, update: LongTermMemoryUpdate):
        """Update long-term memory by agent_id and message_id"""
        result = await self.long_term.update(update)
        
        if result:
            result["storage"] = "mongodb"
        
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
        """Delete long-term memory"""
        
        # If semantic, delete only from ChromaDB
        if memory_type == LongTermType.SEMANTIC:
            if message_id:
                deleted = await self.semantic.delete_by_message_id(agent_id, message_id)
                
                return {
                    "status": "deleted" if deleted else "not_found",
                    "agent_id": agent_id,
                    "memory_type": memory_type.value,
                    "message_id": message_id,
                    "deleted_count": 1 if deleted else 0,
                    "storage": "chromadb_only"
                }
            else:
                count = await self.semantic.delete_all(agent_id)
                
                return {
                    "status": "deleted_all",
                    "agent_id": agent_id,
                    "memory_type": memory_type.value,
                    "deleted_count": count,
                    "storage": "chromadb_only"
                }
        
        # For episodic/procedural - delete from MongoDB
        if message_id:
            deleted = await self.long_term.delete_by_message_id(memory_type, agent_id, message_id)
            
            return {
                "status": "deleted" if deleted else "not_found",
                "agent_id": agent_id,
                "memory_type": memory_type.value,
                "message_id": message_id,
                "deleted_count": 1 if deleted else 0,
                "storage": "mongodb"
            }
        else:
            count = await self.long_term.delete_all(memory_type, agent_id)
            
            return {
                "status": "deleted_all",
                "agent_id": agent_id,
                "memory_type": memory_type.value,
                "deleted_count": count,
                "storage": "mongodb"
            }
    
    async def search_semantic(self, agent_id: str, query: str, k: int = 10):
        """Search semantic memories using vector similarity"""
        return await self.semantic.similarity_search(agent_id, query, self.embed, k)

    async def persist_working_memory(self, agent_id: str, workflow_id: str) -> List[str]:
        """Persist working memories from short-term (Redis) to long-term (MongoDB)"""
        working_memories = await self.short_term.get_many(
            ShortTermType.WORKING, agent_id, workflow_id=workflow_id
        )
        
        persisted_ids = []
        for wm in working_memories:
            long_term_mem = LongTermMemory(
                agent_id=wm["agent_id"],
                memory=wm["memory"],
                memory_type=LongTermType.EPISODIC,
                subtype="working_persisted",
                run_id=wm.get("run_id"),
                workflow_id=wm.get("workflow_id"),
                stages=wm.get("stages", []),
                current_stage=wm.get("current_stage"),
                context_log_summary=wm.get("context_log_summary"),
                user_query=wm.get("user_query"),
                created_at=datetime.utcnow(),
                persisted_at=datetime.utcnow(),
                original_ttl=wm["ttl"]
            )
            
            long_term_mem.message_id = wm["message_id"]
            
            await self.long_term.create(long_term_mem)
            persisted_ids.append(wm["message_id"])
        
        return persisted_ids