from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from ...memory.service import MemoryService
from ..deps import get_memory_service
from ...memory.types import ShortTermMemory, ShortTermType, ShortTermMemoryUpdate

router = APIRouter(prefix="/short-term", tags=["short-term"])

# ==================== CACHE ====================

@router.post("/cache", summary="Add cache memory",
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
                            "memory_type": {"type": "string", "enum": ["cache"], "default": "cache"},
                            "ttl": {"type": "integer", "default": 600},
                            "run_id": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
)
async def add_cache(
    m: ShortTermMemory,
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Store short-term cache memory in Redis with TTL (default: 600 seconds).
    memory_type is automatically set to 'cache' for this endpoint.
    Returns message_id which you can use for retrieval and updates.
    """
    m.memory_type = ShortTermType.CACHE  # Force cache type
    return await svc.add_short_term(m)

@router.get("/cache", summary="Get cache memories")
async def get_cache(
    agent_id: str = Query(..., description="Agent ID (required)"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """Retrieve short-term cache memories from Redis"""
    return await svc.get_short_term(ShortTermType.CACHE, agent_id, message_id, run_id)

@router.patch("/cache", summary="Update cache memory",
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
                            "memory_type": {"type": "string", "enum": ["cache"], "default": "cache"},
                            "memory_updates": {"type": "object"},
                            "remove_keys": {"type": "array", "items": {"type": "string"}},
                            "ttl": {"type": "integer"}
                        }
                    }
                }
            }
        }
    }
)
async def update_cache(
    update: ShortTermMemoryUpdate,
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Update cache memory by agent_id and message_id.
    memory_type is automatically set to 'cache' for this endpoint.
    - memory_updates: Dict of key-value pairs to update or add
    - remove_keys: List of keys to remove from memory
    """
    update.memory_type = ShortTermType.CACHE  # Force cache type
    
    result = await svc.update_short_term(update)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found with given agent_id and message_id")
    
    return {"status": "updated", "memory": result}

# ==================== WORKING ====================

@router.post("/working", summary="Add working memory",
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
                            "memory_type": {"type": "string", "enum": ["working"], "default": "working"},
                            "ttl": {"type": "integer", "default": 600},
                            "run_id": {"type": "string"},
                            "workflow_id": {"type": "string"},
                            "stages": {"type": "array", "items": {"type": "string"}},
                            "current_stage": {"type": "string"},
                            "context_log_summary": {"type": "string"},
                            "user_query": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
)
async def add_working(
    m: ShortTermMemory,
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Store short-term working memory in Redis with workflow context and TTL (default: 600 seconds).
    memory_type is automatically set to 'working' for this endpoint.
    Returns message_id which you can use for retrieval and updates.
    Include workflow_id, stages, current_stage, context_log_summary, user_query for workflow tracking.
    """
    m.memory_type = ShortTermType.WORKING  # Force working type
    return await svc.add_short_term(m)

@router.get("/working", summary="Get working memories")
async def get_working(
    agent_id: str = Query(..., description="Agent ID (required)"),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    message_id: Optional[str] = Query(None, description="Filter by message ID"),
    run_id: Optional[str] = Query(None, description="Filter by run ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """Retrieve short-term working memories from Redis"""
    return await svc.get_short_term(ShortTermType.WORKING, agent_id, message_id, run_id, workflow_id)

@router.patch("/working", summary="Update working memory",
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
                            "memory_type": {"type": "string", "enum": ["working"], "default": "working"},
                            "memory_updates": {"type": "object"},
                            "remove_keys": {"type": "array", "items": {"type": "string"}},
                            "workflow_id": {"type": "string"},
                            "stages": {"type": "array", "items": {"type": "string"}},
                            "current_stage": {"type": "string"},
                            "context_log_summary": {"type": "string"},
                            "user_query": {"type": "string"},
                            "ttl": {"type": "integer"}
                        }
                    }
                }
            }
        }
    }
)
async def update_working(
    update: ShortTermMemoryUpdate,
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Update working memory by agent_id and message_id.
    memory_type is automatically set to 'working' for this endpoint.
    Can update memory dictionary, workflow fields, and reset TTL.
    """
    update.memory_type = ShortTermType.WORKING  # Force working type
    
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
    Persist all working memories for a specific workflow_id from Redis (short-term) 
    to MongoDB (long-term storage as episodic memory with subtype='working_persisted').
    Returns list of message_ids that were persisted.
    """
    persisted_ids = await svc.persist_working_memory(agent_id, workflow_id)
    return {
        "status": "success",
        "agent_id": agent_id,
        "workflow_id": workflow_id,
        "persisted_count": len(persisted_ids),
        "persisted_message_ids": persisted_ids
    }

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