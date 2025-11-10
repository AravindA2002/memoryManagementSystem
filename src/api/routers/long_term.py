from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from ..deps import get_memory_service
from ...memory.service import MemoryService
from ...memory.types import LongTermMemory, LongTermType, LongTermMemoryUpdate
from ..schemas.associative import EntityIn, RelationIn

router = APIRouter(prefix="/long-term", tags=["long-term"])

# ==================== SEMANTIC ====================

@router.post("/semantic", summary="Add semantic memory")
async def add_semantic(
    m: LongTermMemory,
    svc: MemoryService = Depends(get_memory_service)
):
    """
    Store semantic memory permanently in MongoDB and Chroma for vector search.
    memory_type is automatically set to 'semantic' for this endpoint.
    Returns message_id which you can use for retrieval and updates.
    """
    m.memory_type = LongTermType.SEMANTIC  # Force semantic type
    return await svc.add_long_term(m)

@router.get("/semantic", summary="Search semantic memories")
async def search_semantic(
    agent_id: str = Query(..., description="Agent ID"),
    query: str = Query(..., description="Search query"),
    k: int = Query(10, ge=1, le=100, description="Number of results"),
    svc: MemoryService = Depends(get_memory_service),
):
    """Search semantic memories using vector similarity (Chroma)"""
    return await svc.search_semantic(agent_id, query, k)

@router.patch("/semantic", summary="Update semantic memory")
async def update_semantic(
    update: LongTermMemoryUpdate,
    svc: MemoryService = Depends(get_memory_service)
):
    """
    Update semantic memory by agent_id and message_id.
    memory_type is automatically set to 'semantic' for this endpoint.
    """
    update.memory_type = LongTermType.SEMANTIC  # Force semantic type
    
    result = await svc.update_long_term(update)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found with given agent_id and message_id")
    
    return {"status": "updated", "memory": result}

# ==================== EPISODIC (APPEND-ONLY) ====================

@router.post("/episodic", summary="Add episodic memory", 
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["agent_id", "memory"],
                        "properties": {
                            "agent_id": {"type": "string"},
                            "memory": {"type": "object"},
                            "memory_type": {"type": "string", "enum": ["episodic"], "default": "episodic"},
                            "run_id": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "metadata": {"type": "object"},
                            "subtype": {"type": "string", "enum": ["conversational", "summaries", "observations"]},
                            "conversation_id": {"type": "string"},
                            "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                            "turn_index": {"type": "integer"},
                            "observation_id": {"type": "string"},
                            "event": {"type": "string"},
                            "result": {"type": "string"},
                            "reward": {"type": "number"},
                            "credibility": {"type": "number"},
                            "source": {"type": "string"},
                            "summary_type": {"type": "string", "enum": ["extractive", "abstractive"]},
                            "quality_score": {"type": "number"}
                        }
                    }
                }
            }
        }
    }
)
async def add_episodic(
    m: LongTermMemory,
    svc: MemoryService = Depends(get_memory_service)
):
    """
    Store episodic memory permanently in MongoDB (APPEND-ONLY).
    memory_type is automatically set to 'episodic' for this endpoint.
    Returns message_id which you can use for retrieval.
    
    Episodic memories are immutable and cannot be updated after creation.
    
    Available Subtypes:
    - conversational: Chat/dialogue interactions
    - summaries: Conversation or event summaries
    - observations: Agent observations and learnings
    
    Note: 'working_persisted' subtype can only be created via POST /short-term/working/persist endpoint.
    """
    m.memory_type = LongTermType.EPISODIC  # Force episodic type
    
    # Prevent manual creation of working_persisted
    if m.subtype == "working_persisted":
        raise HTTPException(
            status_code=400, 
            detail="Cannot manually create 'working_persisted' episodic memory. Use POST /short-term/working/persist to persist working memory."
        )
    
    return await svc.add_long_term(m)

@router.get("/episodic", summary="Get episodic memories")
async def get_episodic(
    agent_id: str = Query(..., description="Agent ID (required)"),
    subtype: Optional[str] = Query(None, description="Subtype: conversational, summaries, observations, working_persisted"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Retrieve episodic memories from MongoDB.
    
    Episodic memories are append-only and cannot be modified after creation.
    """
    return await svc.get_long_term(
        LongTermType.EPISODIC, agent_id, subtype, 
        message_id, run_id, workflow_id, conversation_id
    )

# NOTE: No PATCH endpoint for episodic - it's append-only!

# ==================== PROCEDURAL ====================

@router.post("/procedural", summary="Add procedural memory",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["agent_id", "memory"],
                        "properties": {
                            "agent_id": {"type": "string"},
                            "memory": {"type": "object"},
                            "memory_type": {"type": "string", "enum": ["procedural"], "default": "procedural"},
                            "run_id": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "metadata": {"type": "object"},
                            "subtype": {"type": "string", "enum": ["agent_store", "tool_store", "workflow_store"]},
                            "name": {"type": "string"},
                            "config": {"type": "object"},
                            "integration": {"type": "object"},
                            "status": {"type": "string", "enum": ["active", "deprecated"]},
                            "change_note": {"type": "string"},
                            "steps": {"type": "array", "items": {"type": "object"}}
                        }
                    }
                }
            }
        }
    }
)
async def add_procedural(
    m: LongTermMemory,
    svc: MemoryService = Depends(get_memory_service)
):
    """
    Store procedural memory permanently in MongoDB.
    memory_type is automatically set to 'procedural' for this endpoint.
    Returns message_id which you can use for retrieval and updates.
    Use subtype: 'agent_store', 'tool_store', or 'workflow_store'.
    """
    m.memory_type = LongTermType.PROCEDURAL  # Force procedural type
    return await svc.add_long_term(m)

@router.get("/procedural", summary="Get procedural memories")
async def get_procedural(
    agent_id: str = Query(..., description="Agent ID (required)"),
    subtype: Optional[str] = Query(None, description="Subtype: agent_store, tool_store, workflow_store"),
    name: Optional[str] = Query(None, description="Filter by name"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """Retrieve procedural memories from MongoDB"""
    return await svc.get_long_term(
        LongTermType.PROCEDURAL, agent_id, subtype, 
        message_id, run_id, name=name
    )

@router.patch("/procedural", summary="Update procedural memory",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["agent_id", "message_id"],
                        "properties": {
                            "agent_id": {"type": "string"},
                            "message_id": {"type": "string"},
                            "memory_type": {"type": "string", "enum": ["procedural"], "default": "procedural"},
                            "memory_updates": {"type": "object"},
                            "remove_keys": {"type": "array", "items": {"type": "string"}},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "metadata_updates": {"type": "object"},
                            "subtype": {"type": "string", "enum": ["agent_store", "tool_store", "workflow_store"]},
                            "name": {"type": "string"},
                            "status": {"type": "string", "enum": ["active", "deprecated"]},
                            "config_updates": {"type": "object"}
                        }
                    }
                }
            }
        }
    }
)
async def update_procedural(
    update: LongTermMemoryUpdate,
    svc: MemoryService = Depends(get_memory_service)
):
    """
    Update procedural memory by agent_id and message_id.
    memory_type is automatically set to 'procedural' for this endpoint.
    """
    update.memory_type = LongTermType.PROCEDURAL  # Force procedural type
    
    result = await svc.update_long_term(update)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"status": "updated", "memory": result}

# ==================== ASSOCIATIVE (Neo4j Only) ====================

@router.post("/associative/entity", summary="Create/Update entity in Neo4j")
def upsert_entity(payload: EntityIn, svc = Depends(get_memory_service)):
    """Create or update an entity node in Neo4j graph database"""
    svc.associative.upsert_entity(payload.name, payload.labels, payload.props)
    return {"status": "ok", "entity": payload.name}

@router.get("/associative/entity/{name}", summary="Get entity from Neo4j")
def get_entity(name: str, svc = Depends(get_memory_service)):
    """Get an entity by name from Neo4j graph database"""
    data = svc.associative.get_entity(name)
    return {"found": data is not None, "entity": data}

@router.post("/associative/relation", summary="Create/Update relation in Neo4j")
def upsert_relation(payload: RelationIn, svc = Depends(get_memory_service)):
    """Create or update a relationship between two entities in Neo4j"""
    rel_type = payload.relation.strip().upper().replace(" ", "_")
    svc.associative.upsert_entity(payload.source)   
    svc.associative.upsert_entity(payload.target)
    svc.associative.upsert_relation(payload.source, rel_type, payload.target, payload.props)
    return {"status": "ok", "source": payload.source, "relation": rel_type, "target": payload.target}

@router.get("/associative/outbound", summary="Get outbound relations from Neo4j")
def get_outbound(name: str = Query(..., description="Entity name"), svc = Depends(get_memory_service)):
    """List all outbound relations from an entity in Neo4j"""
    return {"source": name, "outbound": svc.associative.get_outbound(name)}

@router.get("/associative/inbound", summary="Get inbound relations from Neo4j")
def get_inbound(name: str = Query(..., description="Entity name"), svc = Depends(get_memory_service)):
    """List all inbound relations to an entity in Neo4j"""
    return {"target": name, "inbound": svc.associative.get_inbound(name)}

@router.get("/associative/path", summary="Find path between entities in Neo4j")
def find_path(
    a: str = Query(..., description="Source entity"), 
    b: str = Query(..., description="Target entity"), 
    max_hops: int = Query(4, ge=1, le=10, description="Maximum hops"),
    svc = Depends(get_memory_service)
):
    """Find shortest path between two entities in Neo4j graph"""
    return {"a": a, "b": b, "paths": svc.associative.path_between(a, b, max_hops)}

# ==================== DELETE OPERATIONS ====================

@router.delete("/semantic", summary="Delete semantic memory")
async def delete_semantic(
    agent_id: str = Query(..., description="Agent ID (required)"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete (optional - if not provided, deletes ALL semantic memories)"),
    svc: MemoryService = Depends(get_memory_service)
):
    """
    Delete semantic memory from MongoDB (and Chroma).
    - If message_id is provided: Deletes specific memory
    - If message_id is NOT provided: Deletes ALL semantic memories for the agent
    """
    return await svc.delete_long_term(LongTermType.SEMANTIC, agent_id, message_id)

@router.delete("/episodic", summary="Delete episodic memory")
async def delete_episodic(
    agent_id: str = Query(..., description="Agent ID (required)"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete (optional - if not provided, deletes ALL episodic memories)"),
    svc: MemoryService = Depends(get_memory_service)
):
    """
    Delete episodic memory from MongoDB.
    - If message_id is provided: Deletes specific memory
    - If message_id is NOT provided: Deletes ALL episodic memories for the agent
    """
    return await svc.delete_long_term(LongTermType.EPISODIC, agent_id, message_id)

@router.delete("/procedural", summary="Delete procedural memory")
async def delete_procedural(
    agent_id: str = Query(..., description="Agent ID (required)"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete (optional - if not provided, deletes ALL procedural memories)"),
    svc: MemoryService = Depends(get_memory_service)
):
    """
    Delete procedural memory from MongoDB.
    - If message_id is provided: Deletes specific memory
    - If message_id is NOT provided: Deletes ALL procedural memories for the agent
    """
    return await svc.delete_long_term(LongTermType.PROCEDURAL, agent_id, message_id)