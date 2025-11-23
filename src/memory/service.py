from .redis_store import ShortTermStore
from .mongo_longterm import LongTermStore
from .chroma_semantic import ChromaSemanticStore
from .embeddings import openai_embed
from .neo4j_associative import Neo4jAssociativeStore
from .supermemory_semantic import SupermemorySemanticStore
from ..config.settings import SUPERMEMORY_ENABLED
from .associative_wrapper import AssociativeMemoryWrapper
from ..config.settings import REDIS_URL, MONGO_URL, MONGO_DB, CHROMA_HOST, CHROMA_PORT
import json
import uuid
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from .types import (
    ShortTermMemory, ShortTermType, ShortTermMemoryUpdate,
    SemanticMemory, ConversationalMemory, SummariesMemory, ObservationsMemory,
    ProceduralMemory, WorkingMemoryPersisted, WorkingMemoryPersistedUpdate,
    SemanticMemoryStorage, ConversationalMemoryStorage, SummariesMemoryStorage,
    ObservationsMemoryStorage, ProceduralMemoryStorage,
    LongTermMemoryUpdateStorage, LongTermType,
    SemanticMemoryUpdate, ProceduralMemoryUpdate
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

        self.supermemory = None
        if SUPERMEMORY_ENABLED:
            try:
                self.supermemory = SupermemorySemanticStore()
                print("Supermemory initialized successfully")
            except Exception as e:
                print(f"Supermemory initialization failed: {e}")
                print("Supermemory features disabled")
        
        try:
            self.associative = Neo4jAssociativeStore()
            self.associative_wrapper = AssociativeMemoryWrapper(self.associative)
            print("Neo4j and Associative Wrapper initialized")
        except Exception as e:
            print(f"Neo4j connection failed: {e}")
            print("Associative memory features disabled")
            self.associative = None
            self.associative_wrapper = None

    @staticmethod
    def _generate_message_id() -> str:
        """Generate unique message ID with timestamp"""
        timestamp = datetime.utcnow().strftime("%d%m%Y%H%M")
        unique_id = str(uuid.uuid4())[:8]
        return f"msg_{timestamp}_{unique_id}"

    # SHORT TERM MEMORY
    
    async def add_short_term(self, m: ShortTermMemory) -> Dict[str, Any]:
        """Add short-term memory"""
        message_id = self._generate_message_id()
        m.message_id = message_id
        
        result = await self.short_term.create(m)
        created_at_str = result.created_at.strftime("%d-%m-%Y %H:%M")
        
        return {
            "message_id": message_id,
            "agent_id": m.agent_id,
            "memory_type": m.memory_type.value,
            "created_at": created_at_str,
            "ttl": m.ttl
        }
    
    async def update_short_term(self, update: ShortTermMemoryUpdate):
        """Update short-term memory"""
        return await self.short_term.update(update)
    
    async def get_short_term(
        self, 
        memory_type: ShortTermType,
        agent_id: str, 
        message_id: Optional[str] = None,
        run_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ):
        """Retrieve short-term memories"""
        return await self.short_term.get_many(memory_type, agent_id, message_id, run_id, workflow_id)

    async def delete_short_term(
        self,
        memory_type: ShortTermType,
        agent_id: str,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete short-term memory"""
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
        
    async def add_supermemory(
        self,
        agent_id: str,
        content: str,
        message_id: str,
        spaces: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add memory to Supermemory"""
        if not self.supermemory:
            raise ValueError("Supermemory is not enabled")
        
        result = await self.supermemory.add(
            agent_id=agent_id,
            content=content,
            message_id=message_id,
            metadata=metadata,
            spaces=spaces
        )
        
        return {
            "message_id": message_id,
            "agent_id": agent_id,
            "memory_type": "semantic_supermemory",
            "supermemory_id": result.get("id"),
            "created_at": datetime.utcnow().strftime("%d-%m-%Y %H:%M"),
            "storage": "supermemory"
        }
    
    async def search_supermemory(
        self,
        agent_id: str,
        query: str,
        limit: int = 10,
        spaces: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search memories in Supermemory"""
        if not self.supermemory:
            raise ValueError("Supermemory is not enabled")
        
        return await self.supermemory.search(
            agent_id=agent_id,
            query=query,
            limit=limit,
            spaces=spaces
        )
    
    async def delete_supermemory(
        self,
        agent_id: str,
        message_id: Optional[str] = None,
        memory_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete memory from Supermemory"""
        if not self.supermemory:
            raise ValueError("Supermemory is not enabled")
        
        if memory_id:
            deleted = await self.supermemory.delete(memory_id)
            return {
                "status": "deleted" if deleted else "not_found",
                "agent_id": agent_id,
                "memory_type": "semantic_supermemory",
                "memory_id": memory_id,
                "deleted_count": 1 if deleted else 0
            }
        elif message_id:
            deleted = await self.supermemory.delete_by_message_id(agent_id, message_id)
            return {
                "status": "deleted" if deleted else "not_found",
                "agent_id": agent_id,
                "memory_type": "semantic_supermemory",
                "message_id": message_id,
                "deleted_count": 1 if deleted else 0
            }
        else:
            raise ValueError("Either memory_id or message_id must be provided")

    # LONG TERM MEMORY
    
    async def add_long_term(self, m: Union[SemanticMemory, ConversationalMemory, SummariesMemory, ObservationsMemory, ProceduralMemory]) -> Dict[str, Any]:
        """Add long-term memory"""
        message_id = self._generate_message_id()
        m.message_id = message_id
        
        # Semantic memory: ChromaDB + auto-trigger associative wrapper
        if m.memory_type == LongTermType.SEMANTIC:
            text_to_embed = json.dumps(m.memory, sort_keys=True)
            normalized = m.normalized_text or text_to_embed
            
            await self.semantic.add(
                agent_id=m.agent_id,
                text=text_to_embed,
                normalized_text=normalized,
                embed_fn=self.embed,
                message_id=message_id
            )
            
            associative_result = None
            if self.associative_wrapper:
                try:
                    print(f"Auto-triggering associative wrapper for message_id: {message_id}")
                    
                    if isinstance(m.memory, dict) and "text" in m.memory:
                        memory_text = m.memory["text"]
                    else:
                        memory_text = json.dumps(m.memory, indent=2)
                    
                    print(f"Text to analyze: {memory_text}")
                    associative_result = self.associative_wrapper.process_text(
                        text=memory_text,
                        agent_id=m.agent_id
                    )
                    
                    print(f"Wrapper completed: {associative_result.get('entity_count', 0)} entities, {associative_result.get('relationship_count', 0)} relationships")
                    
                except Exception as e:
                    print(f"Associative wrapper failed: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    associative_result = {
                        "status": "error",
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "entity_count": 0,
                        "relationship_count": 0
                    }
            
            response = {
                "message_id": message_id,
                "agent_id": m.agent_id,
                "memory_type": m.memory_type.value,
                "created_at": datetime.utcnow().strftime("%d-%m-%Y %H:%M"),
                "storage": "chromadb_only"
            }
            
            if associative_result:
                response["associative"] = {
                    "status": associative_result.get("status", "error"),
                    "entities_created": associative_result.get("entity_count", 0),
                    "relationships_created": associative_result.get("relationship_count", 0)
                }
                if associative_result.get("error"):
                    response["associative"]["error"] = associative_result["error"]
            
            return response
        
        # Episodic and procedural: MongoDB with CLEAN storage models
        storage_model = None
        subtype = None
        
        if isinstance(m, ConversationalMemory):
            storage_model = ConversationalMemoryStorage(
                agent_id=m.agent_id,
                memory=m.memory,
                message_id=message_id,
                run_id=m.run_id,
                conversation_id=m.conversation_id,
                role=m.role,
                current_stage=m.current_stage,
                recall_recovery=m.recall_recovery,
                embeddings=m.embeddings
            )
            subtype = "conversational"
        elif isinstance(m, SummariesMemory):
            storage_model = SummariesMemoryStorage(
                agent_id=m.agent_id,
                memory=m.memory,
                message_id=message_id,
                run_id=m.run_id
            )
            subtype = "summaries"
        elif isinstance(m, ObservationsMemory):
            storage_model = ObservationsMemoryStorage(
                agent_id=m.agent_id,
                memory=m.memory,
                message_id=message_id,
                run_id=m.run_id,
                observation_id=m.observation_id,
                observation_kpi=m.observation_kpi,
                recall_recovery=m.recall_recovery,
                embeddings=m.embeddings
            )
            subtype = "observations"
        elif isinstance(m, ProceduralMemory):
            storage_model = ProceduralMemoryStorage(
                agent_id=m.agent_id,
                memory=m.memory,
                message_id=message_id,
                run_id=m.run_id,
                subtype=m.subtype,
                name=m.name,
                config=m.config,
                integration=m.integration,
                status=m.status,
                change_note=m.change_note,
                steps=m.steps
            )
            subtype = m.subtype
        
        if storage_model:
            await self.long_term.create(storage_model)
            created_at = storage_model.created_at
            
            return {
                "message_id": message_id,
                "agent_id": m.agent_id,
                "memory_type": m.memory_type.value,
                "subtype": subtype,
                "created_at": created_at.strftime("%d-%m-%Y %H:%M"),
                "storage": "mongodb"
            }
        
        raise ValueError("Invalid memory type")  # This will never be reached but helps with type checking
    
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
        """Retrieve long-term memories"""
        
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
        
        raw_results = await self.long_term.get_many(
            memory_type, agent_id, subtype, message_id, 
            run_id, workflow_id, conversation_id, name
        )
        
        formatted_results = []
        for doc in raw_results:
            created_at = doc.get("created_at")
            if isinstance(created_at, datetime):
                created_at_str = created_at.strftime("%d-%m-%Y %H:%M")
            elif isinstance(created_at, str):
                created_at_str = created_at
            else:
                created_at_str = datetime.utcnow().strftime("%d-%m-%Y %H:%M")
            
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
    
    async def update_long_term(self, update: Union[SemanticMemoryUpdate, ProceduralMemoryUpdate, LongTermMemoryUpdateStorage]):
        """Update long-term memory"""
        
        if isinstance(update, SemanticMemoryUpdate) or (hasattr(update, 'memory_type') and update.memory_type == LongTermType.SEMANTIC):
            col = self.semantic.get_or_create_collection(update.agent_id)
            
            try:
                results = col.get(where={"message_id": update.message_id})
                
                if not results or not results.get("ids"):
                    return None
                
                existing_doc = results["documents"][0] if results.get("documents") else "{}"
                
                try:
                    existing_memory = json.loads(existing_doc)
                except:
                    existing_memory = {}
                
                if update.memory_updates:
                    existing_memory.update(update.memory_updates)
                
                for key in update.remove_keys:
                    existing_memory.pop(key, None)
                
                updated_text = json.dumps(existing_memory, sort_keys=True)
                normalized = update.normalized_text if update.normalized_text else updated_text
                
                success = await self.semantic.update(
                    agent_id=update.agent_id,
                    message_id=update.message_id,
                    text=updated_text,
                    normalized_text=normalized,
                    embed_fn=self.embed
                )
                
                if not success:
                    return None
                
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
        
        storage_update = update
        if isinstance(update, ProceduralMemoryUpdate):
            storage_update = LongTermMemoryUpdateStorage(
                agent_id=update.agent_id,
                message_id=update.message_id,
                memory_type=LongTermType.PROCEDURAL,
                memory_updates=update.memory_updates,
                remove_keys=update.remove_keys,
                subtype=update.subtype,
                name=update.name,
                config_updates=update.config_updates,
                integration_updates=update.integration_updates,
                status=update.status,
                change_note=update.change_note,
                steps=update.steps
            )
        
        result = await self.long_term.update(storage_update)
        
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

    # WORKING PERSISTED MEMORY
    
    async def persist_working_memory(self, agent_id: str, workflow_id: str) -> Dict[str, Any]:
        """Persist working memories from Redis to MongoDB"""
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
            updated_at = None
            if "metadata" in wm and wm["metadata"].get("updated_at"):
                updated_at_str = wm["metadata"]["updated_at"]
                try:
                    updated_at = datetime.strptime(updated_at_str, "%d-%m-%Y %H:%M")
                except:
                    updated_at = None
            
            persisted_mem = WorkingMemoryPersisted(
                agent_id=wm["agent_id"],
                memory=wm["memory"],
                message_id=wm["message_id"],
                run_id=wm.get("run_id", ""),
                workflow_id=wm.get("workflow_id", ""),
                stages=wm.get("stages", []),
                current_stage=wm.get("current_stage", ""),
                context_log_summary=wm.get("context_log_summary", ""),
                user_query=wm.get("user_query", ""),
                created_at=wm.get("created_at", datetime.utcnow()),
                persisted_at=datetime.utcnow(),
                original_ttl=wm.get("ttl"),
                updated_at=updated_at
            )
            
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
        """Directly add working_persisted memory"""
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
        """Update working_persisted memory"""
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
        """Retrieve working_persisted memories"""
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