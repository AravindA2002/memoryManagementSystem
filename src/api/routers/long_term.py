from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from ..deps import get_memory_service
from ...memory.types import SupermemorySemanticMemory
from ..schemas.openapi_schemas import SUPERMEMORY_POST_SCHEMA
from ...memory.service import MemoryService
from ...memory.types import (
    LongTermType, LongTermMemoryUpdateStorage,
    WorkingMemoryPersisted, WorkingMemoryPersistedUpdate,
    SemanticMemory, ConversationalMemory, SummariesMemory, ObservationsMemory, ProceduralMemory,
    SemanticMemoryUpdate, ProceduralMemoryUpdate,
    SemanticMemoryOut, ConversationalMemoryOut, SummariesMemoryOut, ObservationsMemoryOut
)
from ..schemas.associative import EntityIn, RelationIn
from ..schemas.openapi_schemas import (
    SEMANTIC_POST_SCHEMA, SEMANTIC_PATCH_SCHEMA,
    EPISODIC_CONVERSATIONAL_POST_SCHEMA,
    EPISODIC_SUMMARIES_POST_SCHEMA,
    EPISODIC_OBSERVATIONS_POST_SCHEMA,
    PROCEDURAL_POST_SCHEMA, PROCEDURAL_PATCH_SCHEMA,
    WORKING_PERSISTED_PATCH_SCHEMA
)

router = APIRouter(prefix="/long-term", tags=["long-term"])

# SEMANTIC

@router.post("/semantic", summary="Add semantic memory", openapi_extra=SEMANTIC_POST_SCHEMA)
async def add_semantic(
    m: SemanticMemory,
    svc: MemoryService = Depends(get_memory_service)
):
    """Store semantic memory permanently in Chroma for vector search"""
    m.memory_type = LongTermType.SEMANTIC
    return await svc.add_long_term(m)

@router.get("/semantic", summary="Search semantic memories")
async def search_semantic(
    agent_id: str = Query(..., description="Agent ID"),
    query: str = Query(..., description="Search query"),
    k: int = Query(10, ge=1, le=100, description="Number of results"),
    svc: MemoryService = Depends(get_memory_service),
):
    """Search semantic memories using vector similarity"""
    return await svc.search_semantic(agent_id, query, k)

@router.patch("/semantic", summary="Update semantic memory", openapi_extra=SEMANTIC_PATCH_SCHEMA)
async def update_semantic(
    update: SemanticMemoryUpdate,
    svc: MemoryService = Depends(get_memory_service)
):
    """Update semantic memory by agent_id and message_id"""
    result = await svc.update_long_term(update)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"status": "updated", "memory": result}

@router.delete("/semantic", summary="Delete semantic memory")
async def delete_semantic(
    agent_id: str = Query(..., description="Agent ID"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete"),
    svc: MemoryService = Depends(get_memory_service)
):
    """Delete semantic memory from Chroma"""
    return await svc.delete_long_term(LongTermType.SEMANTIC, agent_id, message_id)

@router.post("/semantic-supermemory", summary="Add semantic memory to Supermemory", openapi_extra=SUPERMEMORY_POST_SCHEMA, response_model=None)
async def add_supermemory_semantic(
    m: SupermemorySemanticMemory,
    svc: MemoryService = Depends(get_memory_service)
):
    """Store semantic memory in Supermemory for AI-native memory storage"""
    if not svc.supermemory:
        raise HTTPException(status_code=503, detail="Supermemory is not enabled. Set SUPERMEMORY_ENABLED=true and SUPERMEMORY_API_KEY in .env")
    
    message_id = svc._generate_message_id()
    
    metadata = {
        "memory": m.memory,
        "run_id": m.run_id,
        **m.metadata_extra
    }
    
    return await svc.add_supermemory(
        agent_id=m.agent_id,
        content=m.content,
        message_id=message_id,
        spaces=m.spaces,
        metadata=metadata
    )

@router.get("/semantic-supermemory", summary="Search Supermemory semantic store")
async def search_supermemory_semantic(
    agent_id: str = Query(..., description="Agent ID"),
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Number of results"),
    spaces: Optional[str] = Query(None, description="Comma-separated space IDs"),
    svc: MemoryService = Depends(get_memory_service)
):
    """Search memories in Supermemory semantic store using Supermemory's rewrite_query"""
    if not svc.supermemory:
        raise HTTPException(status_code=503, detail="Supermemory is not enabled")
    
    space_list = [s.strip() for s in spaces.split(",")] if spaces else None
    return await svc.supermemory.search(agent_id, query, limit, space_list)

@router.delete("/semantic-supermemory", summary="Delete Supermemory semantic memory", response_model=None)
async def delete_supermemory_semantic(
    agent_id: str = Query(..., description="Agent ID"),
    message_id: Optional[str] = Query(None, description="Message ID to delete"),
    memory_id: Optional[str] = Query(None, description="Supermemory memory ID"),
    svc: MemoryService = Depends(get_memory_service)
):
    """Delete semantic memory from Supermemory"""
    if not svc.supermemory:
        raise HTTPException(status_code=503, detail="Supermemory is not enabled")
    
    return await svc.delete_supermemory(agent_id, message_id, memory_id)





# EPISODIC - CONVERSATIONAL

@router.post("/episodic/conversational", summary="Add conversational episodic memory", openapi_extra=EPISODIC_CONVERSATIONAL_POST_SCHEMA,response_model=None)
async def add_episodic_conversational(
    m: ConversationalMemory,
    svc: MemoryService = Depends(get_memory_service)
): 
    """Store conversational episodic memory (append-only)"""
    m.memory_type = LongTermType.EPISODIC
    m.subtype = "conversational"
    return await svc.add_long_term(m)

@router.get("/episodic/conversational", summary="Get conversational episodic memories", response_model=List[ConversationalMemoryOut])
async def get_episodic_conversational(
    agent_id: str = Query(..., description="Agent ID"),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation ID"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """Retrieve conversational episodic memories"""
    return await svc.get_long_term(
        LongTermType.EPISODIC, agent_id, "conversational", 
        message_id, run_id, conversation_id=conversation_id
    )

@router.delete("/episodic/conversational", summary="Delete conversational episodic memory")
async def delete_episodic_conversational(
    agent_id: str = Query(..., description="Agent ID"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete"),
    svc: MemoryService = Depends(get_memory_service)
):
    """Delete conversational episodic memory"""
    return await svc.delete_long_term(LongTermType.EPISODIC, agent_id, message_id)

# EPISODIC - SUMMARIES

@router.post("/episodic/summaries", summary="Add summaries episodic memory", openapi_extra=EPISODIC_SUMMARIES_POST_SCHEMA)
async def add_episodic_summaries(
    m: SummariesMemory,
    svc: MemoryService = Depends(get_memory_service)
):
    """Store summaries episodic memory (append-only)"""
    m.memory_type = LongTermType.EPISODIC
    m.subtype = "summaries"
    return await svc.add_long_term(m)

@router.get("/episodic/summaries", summary="Get summaries episodic memories", response_model=List[SummariesMemoryOut])
async def get_episodic_summaries(
    agent_id: str = Query(..., description="Agent ID"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """Retrieve summaries episodic memories"""
    return await svc.get_long_term(
        LongTermType.EPISODIC, agent_id, "summaries", 
        message_id, run_id
    )

@router.delete("/episodic/summaries", summary="Delete summaries episodic memory")
async def delete_episodic_summaries(
    agent_id: str = Query(..., description="Agent ID"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete"),
    svc: MemoryService = Depends(get_memory_service)
):
    """Delete summaries episodic memory"""
    return await svc.delete_long_term(LongTermType.EPISODIC, agent_id, message_id)

# EPISODIC - OBSERVATIONS

@router.post("/episodic/observations", summary="Add observations episodic memory", openapi_extra=EPISODIC_OBSERVATIONS_POST_SCHEMA)
async def add_episodic_observations(
    m: ObservationsMemory,
    svc: MemoryService = Depends(get_memory_service)
):
    """Store observations episodic memory (append-only)"""
    m.memory_type = LongTermType.EPISODIC
    m.subtype = "observations"
    return await svc.add_long_term(m)

@router.get("/episodic/observations", summary="Get observations episodic memories", response_model=List[ObservationsMemoryOut])
async def get_episodic_observations(
    agent_id: str = Query(..., description="Agent ID"),
    observation_id: Optional[str] = Query(None, description="Filter by observation ID"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """Retrieve observations episodic memories"""
    return await svc.get_long_term(
        LongTermType.EPISODIC, agent_id, "observations", 
        message_id, run_id
    )

@router.delete("/episodic/observations", summary="Delete observations episodic memory")
async def delete_episodic_observations(
    agent_id: str = Query(..., description="Agent ID"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete"),
    svc: MemoryService = Depends(get_memory_service)
):
    """Delete observations episodic memory"""
    return await svc.delete_long_term(LongTermType.EPISODIC, agent_id, message_id)

# PROCEDURAL

@router.post("/procedural", summary="Add procedural memory", openapi_extra=PROCEDURAL_POST_SCHEMA)
async def add_procedural(
    m: ProceduralMemory,
    svc: MemoryService = Depends(get_memory_service)
):
    """Store procedural memory permanently in MongoDB"""
    m.memory_type = LongTermType.PROCEDURAL
    return await svc.add_long_term(m)

@router.get("/procedural", summary="Get procedural memories")
async def get_procedural(
    agent_id: str = Query(..., description="Agent ID"),
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

@router.patch("/procedural", summary="Update procedural memory", openapi_extra=PROCEDURAL_PATCH_SCHEMA)
async def update_procedural(
    update: ProceduralMemoryUpdate,
    svc: MemoryService = Depends(get_memory_service)
):
    """Update procedural memory by agent_id and message_id"""
    result = await svc.update_long_term(update)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"status": "updated", "memory": result}

@router.delete("/procedural", summary="Delete procedural memory")
async def delete_procedural(
    agent_id: str = Query(..., description="Agent ID"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete"),
    svc: MemoryService = Depends(get_memory_service)
):
    """Delete procedural memory from MongoDB"""
    return await svc.delete_long_term(LongTermType.PROCEDURAL, agent_id, message_id)

# WORKING PERSISTED

@router.get("/working-persisted", summary="Get working persisted memories")
async def get_working_persisted(
    agent_id: str = Query(..., description="Agent ID"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """Retrieve working_persisted memories from MongoDB"""
    return await svc.get_working_persisted(agent_id, workflow_id, message_id, run_id)

@router.patch("/working-persisted", summary="Update working persisted memory", openapi_extra=WORKING_PERSISTED_PATCH_SCHEMA)
async def update_working_persisted(
    update: WorkingMemoryPersistedUpdate,
    svc: MemoryService = Depends(get_memory_service)
):
    """Update working_persisted memory by agent_id and message_id"""
    result = await svc.update_working_persisted(update)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    return {"status": "updated", "memory": result}

@router.delete("/working-persisted", summary="Delete working persisted memory")
async def delete_working_persisted(
    agent_id: str = Query(..., description="Agent ID"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete"),
    svc: MemoryService = Depends(get_memory_service)
):
    """Delete working_persisted memory from MongoDB"""
    return await svc.delete_working_persisted(agent_id, message_id)

# ASSOCIATIVE (Neo4j)

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