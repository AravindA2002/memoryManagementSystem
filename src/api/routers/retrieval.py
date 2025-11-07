# src/api/routers/retrieval.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from ...memory.service import MemoryService
from ..deps import get_memory_service

router = APIRouter(prefix="/retrieve", tags=["retrieve"])

# -------- Semantic (similarity search) --------
@router.get("/semantic", summary="Semantic similarity search (Chroma)")
async def search_semantic(
    agent_id: str = Query(..., description="Agent/collection id"),
    query: str = Query(..., description="Search query"),
    k: int = Query(10, ge=1, le=100),
    svc: MemoryService = Depends(get_memory_service),
):
    return await svc.search_semantic(agent_id, query, k)

# -------- Episodic (Mongo) --------
@router.get("/episodic/conversational", summary="List episodic conversational memories")
async def get_ep_conversational(
    agent_id: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    svc: MemoryService = Depends(get_memory_service),
):
    return await svc.get_ep_conversational(agent_id, limit)

@router.get("/episodic/summaries", summary="List episodic summaries")
async def get_ep_summaries(
    agent_id: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    svc: MemoryService = Depends(get_memory_service),
):
    return await svc.get_ep_summaries(agent_id, limit)

@router.get("/episodic/observations", summary="List episodic observations")
async def get_ep_observations(
    agent_id: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    svc: MemoryService = Depends(get_memory_service),
):
    return await svc.get_ep_observations(agent_id, limit)

# -------- Procedural (Mongo) --------
@router.get("/procedural/agents", summary="List procedural agents")
async def get_proc_agents(
    agent_id: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    svc: MemoryService = Depends(get_memory_service),
):
    return await svc.get_proc_agents(agent_id, limit)

@router.get("/procedural/tools", summary="List procedural tools")
async def get_proc_tools(
    agent_id: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    svc: MemoryService = Depends(get_memory_service),
):
    return await svc.get_proc_tools(agent_id, limit)

@router.get("/procedural/workflows", summary="List procedural workflows")
async def get_proc_workflows(
    agent_id: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    svc: MemoryService = Depends(get_memory_service),
):
    return await svc.get_proc_workflows(agent_id, limit)

# -------- Short-term / Working (Redis) --------
@router.get("/short-term", summary="List short-term memories (Redis)")
async def get_short_term(
    agent_id: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    svc: MemoryService = Depends(get_memory_service),
):
    return await svc.get_short_term(agent_id, limit)

@router.get("/working", summary="List working memories (Redis)")
async def get_working(
    agent_id: str = Query(...),
    limit: int = Query(50, ge=1, le=500),
    svc: MemoryService = Depends(get_memory_service),
):
    return await svc.get_working(agent_id, limit)
