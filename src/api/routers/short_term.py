from fastapi import APIRouter, Depends, Query, HTTPException, Body
from fastapi.routing import APIRoute
from typing import Optional
from ...memory.service import MemoryService
from ..deps import get_memory_service
from ...memory.types import (
    ShortTermMemory, ShortTermType, ShortTermMemoryUpdate,
    CacheMemory, WorkingMemory
)
from ..schemas.openapi_schemas import (
    CACHE_POST_SCHEMA, CACHE_PATCH_SCHEMA,
    WORKING_POST_SCHEMA, WORKING_PATCH_SCHEMA
)

class NoSchemaRoute(APIRoute):
    """Custom route that doesn't generate schema from Pydantic models"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove model schema generation
        if hasattr(self, 'body_field'):
            self.body_field = None

# Use custom route class
router = APIRouter(prefix="/short-term", tags=["short-term"], route_class=NoSchemaRoute)

# ==================== CACHE ====================

@router.post("/cache", summary="Add cache memory", openapi_extra=CACHE_POST_SCHEMA)
async def add_cache(
    m: CacheMemory,
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Store short-term cache memory in Redis with TTL (default: 600 seconds = 10 mins).
    Returns message_id which you can use for retrieval and updates.
    
    Clean schema: Only stores agent_id, memory, ttl, run_id (no unnecessary fields).
    """
    # Convert to generic for service compatibility
    
    generic = ShortTermMemory(**m.model_dump())
    return await svc.add_short_term(generic)

@router.get("/cache", summary="Get cache memories")
async def get_cache(
    agent_id: str = Query(..., description="Agent ID (required)"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Retrieve short-term cache memories from Redis.
    
    Returns clean schema with metadata:
    - created_at: Always present
    - updated_at: Only present if memory was updated
    """
    return await svc.get_short_term(ShortTermType.CACHE, agent_id, message_id, run_id)

@router.patch("/cache", summary="Update cache memory", openapi_extra=CACHE_PATCH_SCHEMA)
async def update_cache(
    update: ShortTermMemoryUpdate ,
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Update cache memory by agent_id and message_id.
    Sets updated_at timestamp in metadata.
    - memory_updates: Dict of key-value pairs to update or add
    - remove_keys: List of keys to remove from memory
    """
    update.memory_type = ShortTermType.CACHE
    
    result = await svc.update_short_term(update)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found with given agent_id and message_id")
    
    return {"status": "updated", "memory": result}

# ==================== WORKING ====================

@router.post("/working", summary="Add working memory", openapi_extra=WORKING_POST_SCHEMA)
async def add_working(
    m: WorkingMemory ,
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Store short-term working memory in Redis with workflow context (default TTL: 600s = 10 mins).
    
    Clean schema: Stores agent_id, memory, ttl, run_id, workflow_id, stages, 
                  current_stage, context_log_summary, user_query.
    """
    # Convert to generic for service compatibility
    generic = ShortTermMemory(**m.model_dump())
    return await svc.add_short_term(generic)

@router.get("/working", summary="Get working memories")
async def get_working(
    agent_id: str = Query(..., description="Agent ID (required)"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Retrieve short-term working memories from Redis.
    
    Returns clean schema with workflow fields and metadata:
    - created_at: Always present
    - updated_at: Only present if memory was updated
    """
    return await svc.get_short_term(ShortTermType.WORKING, agent_id, message_id, run_id, workflow_id)

@router.patch("/working", summary="Update working memory",openapi_extra=WORKING_PATCH_SCHEMA)
async def update_working(
    update: ShortTermMemoryUpdate ,
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Update working memory by agent_id and message_id.
    Can update memory dict, workflow fields, and TTL.
    Sets updated_at timestamp in metadata.
    """
    update.memory_type = ShortTermType.WORKING
    
    result = await svc.update_short_term(update)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found with given agent_id and message_id")
    
    return {"status": "updated", "memory": result}

@router.post("/working/persist", summary="Persist working memory to long-term")
async def persist_working_memory(
    agent_id: str = Query(..., description="Agent ID"),
    workflow_id: str = Query(..., description="Workflow ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Persist all working memories for a workflow from Redis (short-term) 
    to MongoDB (long-term storage in separate lt_working_persisted collection).
    
    NEW: Working persisted memories are now stored in their own collection
    with the same schema as short-term working memory, NOT under episodic.
    
    Returns list of message_ids that were persisted.
    """
    return await svc.persist_working_memory(agent_id, workflow_id)

# ==================== DELETE OPERATIONS ====================

@router.delete("/cache", summary="Delete cache memory")
async def delete_cache(
    agent_id: str = Query(..., description="Agent ID (required)"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete (optional - if not provided, flushes all cache)"),
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Delete cache memory from Redis.
    - If message_id is provided: Deletes specific memory
    - If message_id is NOT provided: Flushes ALL cache memories for the agent
    """
    return await svc.delete_short_term(ShortTermType.CACHE, agent_id, message_id)

@router.delete("/working", summary="Delete working memory")
async def delete_working(
    agent_id: str = Query(..., description="Agent ID (required)"),
    message_id: Optional[str] = Query(None, description="Specific message ID to delete (optional - if not provided, flushes all working memory)"),
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Delete working memory from Redis.
    - If message_id is provided: Deletes specific memory
    - If message_id is NOT provided: Flushes ALL working memories for the agent
    """
    return await svc.delete_short_term(ShortTermType.WORKING, agent_id, message_id)