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
    LongTermMemory, LongTermType, LongTermMemoryUpdate,
    WorkingMemoryPersisted, WorkingMemoryPersistedUpdate  # NEW IMPORTS
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
            "created_at": created_at_str,
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
                "created_at": datetime.utcnow().strftime("%d-%m-%Y %H:%M"),  # Generate here, not from model
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
        # Convert to legacy LongTermMemory for storage if needed
        if not hasattr(m, 'created_at'):
            # Create a new instance with created_at
            from .types import LongTermMemory as LegacyLongTermMemory
            
            storage_model = LegacyLongTermMemory(
                agent_id=m.agent_id,
                memory=m.memory,
                memory_type=m.memory_type,
                message_id=message_id,
                run_id=getattr(m, 'run_id', None),
                subtype=getattr(m, 'subtype', None),
                # Episodic conversational fields
                conversation_id=getattr(m, 'conversation_id', None),
                role=getattr(m, 'role', None),
                current_stage=getattr(m, 'current_stage', None),
                recall_recovery=getattr(m, 'recall_recovery', None),
                embeddings=getattr(m, 'embeddings', []),
                # Episodic observations fields
                observation_id=getattr(m, 'observation_id', None),
                observation_kpi=getattr(m, 'observation_kpi', None),
                # Procedural fields
                name=getattr(m, 'name', None),
                config=getattr(m, 'config', {}),
                integration=getattr(m, 'integration', {}),
                status=getattr(m, 'status', None),
                change_note=getattr(m, 'change_note', None),
                steps=getattr(m, 'steps', [])
            )
            
            await self.long_term.create(storage_model)
            created_at = storage_model.created_at
        else:
            await self.long_term.create(m)
            created_at = m.created_at
        
        # Get subtype safely (only episodic and procedural have subtypes)
        subtype = getattr(m, 'subtype', None)
        
        return {
            "message_id": message_id,
            "agent_id": m.agent_id,
            "memory_type": m.memory_type.value,
            "subtype": subtype,
            "created_at": created_at.strftime("%d-%m-%Y %H:%M"),  # Use the created_at from storage model
            "storage": "mongodb"
        }
    
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
        """Retrieve long-term memories and format according to output schemas"""
        
        # Handle semantic memory separately (stored in ChromaDB)
        if memory_type == LongTermType.SEMANTIC:
            col = self.semantic.get_or_create_collection(agent_id)
            
            query_filter = {}
            if message_id:
                query_filter["message_id"] = message_id
            if run_id:
                query_filter["run_id"] = run_id
            
            try:
                if query_filter:
                    results = col.get(where=query_filter)
                else:
                    results = col.get()
                
                memories = []
                if results and results.get("ids"):
                    for i, doc_id in enumerate(results["ids"]):
                        metadata = results["metadatas"][i] if results.get("metadatas") and i < len(results["metadatas"]) else {}
                        doc = results["documents"][i] if results.get("documents") and i < len(results["documents"]) else "{}"
                        
                        item = {
                            "agent_id": agent_id,
                            "message_id": metadata.get("message_id", ""),
                            "memory": json.loads(doc) if doc else {},
                            "memory_type": "semantic",
                            "run_id": metadata.get("run_id"),
                            "metadata": {
                                "created_at": metadata.get("created_at") or datetime.utcnow().strftime("%d-%m-%Y %H:%M"),
                                "updated_at": metadata.get("updated_at")
                            }
                        }
                        memories.append(item)
                
                return memories
                
            except Exception as e:
                print(f"Error retrieving semantic memories: {e}")
                return []
        
        # For episodic and procedural - retrieve from MongoDB
        raw_results = await self.long_term.get_many(
            memory_type, agent_id, subtype, message_id, 
            run_id, workflow_id, conversation_id, name
        )
        
        # Format results according to output schemas
        formatted_results = []
        for doc in raw_results:
            # Handle created_at - ensure it's always a string
            created_at = doc.get("created_at")
            if isinstance(created_at, datetime):
                created_at_str = created_at.strftime("%d-%m-%Y %H:%M")
            elif isinstance(created_at, str):
                created_at_str = created_at
            else:
                # Fallback to current time if missing
                created_at_str = datetime.utcnow().strftime("%d-%m-%Y %H:%M")
            
            # Handle updated_at - only include if present
            updated_at = doc.get("updated_at")
            if isinstance(updated_at, datetime):
                updated_at_str = updated_at.strftime("%d-%m-%Y %H:%M")
            elif isinstance(updated_at, str):
                updated_at_str = updated_at
            else:
                updated_at_str = None
            
            formatted_doc = {
                "agent_id": doc.get("agent_id"),
                "memory": doc.get("memory"),
                "memory_type": doc.get("memory_type"),
                "message_id": doc.get("message_id"),
                "run_id": doc.get("run_id"),
                "metadata": {
                    "created_at": created_at_str,
                    "updated_at": updated_at_str
                }
            }
            
            # Add subtype-specific fields
            if memory_type == LongTermType.EPISODIC:
                formatted_doc["subtype"] = doc.get("subtype")
                
                if subtype == "conversational":
                    formatted_doc["conversation_id"] = doc.get("conversation_id", "")
                    formatted_doc["role"] = doc.get("role", "")
                    formatted_doc["current_stage"] = doc.get("current_stage")
                    formatted_doc["recall_recovery"] = doc.get("recall_recovery")
                    formatted_doc["embeddings"] = doc.get("embeddings", [])
                
                elif subtype == "observations":
                    formatted_doc["observation_id"] = doc.get("observation_id", "")
                    formatted_doc["observation_kpi"] = doc.get("observation_kpi")
                    formatted_doc["recall_recovery"] = doc.get("recall_recovery")
                    formatted_doc["embeddings"] = doc.get("embeddings", [])
                
                # summaries has no extra fields
            
            elif memory_type == LongTermType.PROCEDURAL:
                formatted_doc["subtype"] = doc.get("subtype", "")
                formatted_doc["name"] = doc.get("name", "")
                formatted_doc["config"] = doc.get("config", {})
                formatted_doc["integration"] = doc.get("integration", {})
                formatted_doc["status"] = doc.get("status")
                formatted_doc["change_note"] = doc.get("change_note")
                formatted_doc["steps"] = doc.get("steps", [])
            
            formatted_results.append(formatted_doc)
        
        return formatted_results
    async def update_long_term(self, update: LongTermMemoryUpdate):
        """Update long-term memory by agent_id and message_id"""
        
        # Handle semantic memory separately (stored in ChromaDB)
        if update.memory_type == LongTermType.SEMANTIC:
            # Build updated text from memory_updates
            # First, get the existing memory from ChromaDB
            col = self.semantic.get_or_create_collection(update.agent_id)
            
            try:
                results = col.get(where={"message_id": update.message_id})
                
                if not results or not results.get("ids"):
                    return None
                
                # Get existing document
                existing_doc = results["documents"][0] if results.get("documents") else "{}"
                existing_metadata = results["metadatas"][0] if results.get("metadatas") else {}
                
                # Parse existing document as JSON to get memory dict
                import json
                try:
                    existing_memory = json.loads(existing_doc)
                except:
                    existing_memory = {}
                
                # Apply updates
                if update.memory_updates:
                    existing_memory.update(update.memory_updates)
                
                # Remove keys
                for key in update.remove_keys:
                    existing_memory.pop(key, None)
                
                # Convert back to text
                updated_text = json.dumps(existing_memory, sort_keys=True)
                
                # Use normalized_text if provided, otherwise use updated_text
                normalized = update.normalized_text if update.normalized_text else updated_text
                
                # Update in ChromaDB
                success = await self.semantic.update(
                    agent_id=update.agent_id,
                    message_id=update.message_id,
                    text=updated_text,
                    normalized_text=normalized,
                    embed_fn=self.embed
                )
                
                if not success:
                    return None
                
                # Get the updated entry to return
                results = col.get(where={"message_id": update.message_id})
                if results and results.get("ids"):
                    updated_metadata = results["metadatas"][0] if results.get("metadatas") else {}
                    updated_doc = results["documents"][0] if results.get("documents") else "{}"
                    
                    return {
                        "agent_id": update.agent_id,
                        "message_id": update.message_id,
                        "memory_type": "semantic",
                        "memory": json.loads(updated_doc) if updated_doc else {},
                        "created_at": updated_metadata.get("created_at"),
                        "updated_at": updated_metadata.get("updated_at"),
                        "normalized_text": updated_metadata.get("normalized_text"),
                        "storage": "chromadb_only"
                    }
                
                return None
                
            except Exception as e:
                print(f"Error updating semantic memory: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # For episodic and procedural - update in MongoDB
        result = await self.long_term.update(update)
        
        if result:
            result["storage"] = "mongodb"
        
        return result
    
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

  # ==================== WORKING PERSISTED MEMORY (NEW SECTION) ====================

    # ==================== WORKING PERSISTED MEMORY ====================
    
    async def persist_working_memory(self, agent_id: str, workflow_id: str) -> Dict[str, Any]:
        """
        Persist working memories from short-term (Redis) to long-term (MongoDB).
        NOW stores in separate lt_working_persisted collection with same schema as short-term.
        Preserves updated_at timestamp if the memory was updated in Redis.
        """
        working_memories = await self.short_term.get_many(
            ShortTermType.WORKING, agent_id, workflow_id=workflow_id
        )
        
        if not working_memories:
            return {
                "status": "no_memories_found",
                "agent_id": agent_id,
                "workflow_id": workflow_id,
                "persisted_count": 0
            }
        
        persisted_ids = []
        for wm in working_memories:
            # Extract updated_at from metadata if it exists
            updated_at = None
            if "metadata" in wm and wm["metadata"].get("updated_at"):
                # Parse the updated_at string back to datetime
                updated_at_str = wm["metadata"]["updated_at"]
                try:
                    # Parse format: "DD-MM-YYYY HH:MM"
                    updated_at = datetime.strptime(updated_at_str, "%d-%m-%Y %H:%M")
                except:
                    # If parsing fails, leave it as None
                    updated_at = None
            
            # Create WorkingMemoryPersisted with SAME schema as short-term working memory
            from .types import WorkingMemoryPersisted
            
            persisted_mem = WorkingMemoryPersisted(
                agent_id=wm["agent_id"],
                memory=wm["memory"],
                message_id=wm["message_id"],  # Keep same message_id from short-term
                run_id=wm.get("run_id", ""),
                workflow_id=wm.get("workflow_id", ""),
                stages=wm.get("stages", []),
                current_stage=wm.get("current_stage", ""),
                context_log_summary=wm.get("context_log_summary", ""),
                user_query=wm.get("user_query", ""),
                created_at=wm.get("created_at", datetime.utcnow()),
                persisted_at=datetime.utcnow(),
                original_ttl=wm.get("ttl"),
                updated_at=updated_at  # Preserve updated_at if it exists
            )
            
            # Store in separate collection
            doc_id = await self.long_term.create_working_persisted(persisted_mem)
            persisted_ids.append(wm["message_id"])
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "workflow_id": workflow_id,
            "persisted_count": len(persisted_ids),
            "message_ids": persisted_ids,
            "storage": "mongodb_working_persisted"
        }
    
    async def add_working_persisted(self, m) -> Dict[str, Any]:
        """Directly add a working_persisted memory"""
        if not m.message_id:
            m.message_id = self._generate_message_id()
        
        doc_id = await self.long_term.create_working_persisted(m)
        
        return {
            "id": doc_id,
            "message_id": m.message_id,
            "agent_id": m.agent_id,
            "memory_type": "working_persisted",
            "created_at": m.created_at.strftime("%d-%m-%Y %H:%M"),
            "persisted_at": m.persisted_at.strftime("%d-%m-%Y %H:%M"),
            "storage": "mongodb_working_persisted"
        }
    
    async def update_working_persisted(self, update) -> Optional[dict]:
        """Update a working_persisted memory"""
        result = await self.long_term.update_working_persisted(update)
        
        if result:
            result["storage"] = "mongodb_working_persisted"
        
        return result
    
    async def get_working_persisted(
        self,
        agent_id: str,
        workflow_id: Optional[str] = None,
        message_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> List[dict]:
        """Retrieve working_persisted memories from MongoDB"""
        return await self.long_term.get_working_persisted(
            agent_id, workflow_id, message_id, run_id
        )
    
    async def delete_working_persisted(
        self,
        agent_id: str,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete working_persisted memory"""
        if message_id:
            deleted = await self.long_term.delete_working_persisted_by_message_id(agent_id, message_id)
            
            return {
                "status": "deleted" if deleted else "not_found",
                "agent_id": agent_id,
                "memory_type": "working_persisted",
                "message_id": message_id,
                "deleted_count": 1 if deleted else 0,
                "storage": "mongodb_working_persisted"
            }
        else:
            count = await self.long_term.delete_all_working_persisted(agent_id)
            
            return {
                "status": "deleted_all",
                "agent_id": agent_id,
                "memory_type": "working_persisted",
                "deleted_count": count,
                "storage": "mongodb_working_persisted"
            }