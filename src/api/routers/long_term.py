from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from ..deps import get_memory_service
from ...memory.service import MemoryService
from ...memory.types import (
    SemanticCreate,
    EpisodicConversationalCreate, EpisodicSummaryCreate, EpisodicObservationCreate,
    ProceduralAgentCreate, ProceduralToolCreate, ProceduralWorkflowCreate
)
from ..schemas.associative import EntityIn, RelationIn

router = APIRouter(prefix="/long-term", tags=["long-term"])



# ----------- Associative (Neo4j) Endpoints -----------
@router.post("/entity", summary="Create/Update an entity")
def upsert_entity(payload: EntityIn, svc = Depends(get_memory_service)):
    svc.associative.upsert_entity(payload.name, payload.labels, payload.props)
    return {"status": "ok", "entity": payload.name}

@router.get("/entity/{name}", summary="Get an entity by name")
def get_entity(name: str, svc = Depends(get_memory_service)):
    data = svc.associative.get_entity(name)
    return {"found": data is not None, "entity": data}

@router.post("/associate", summary="Create/Update an association (relation) between two entities")
def upsert_association(payload: RelationIn, svc = Depends(get_memory_service)):
    rel_type = payload.relation.strip().upper().replace(" ", "_")
    svc.associative.upsert_entity(payload.source)   
    svc.associative.upsert_entity(payload.target)
    svc.associative.upsert_relation(payload.source, rel_type, payload.target, payload.props)
    return {"status": "ok", "source": payload.source, "relation": rel_type, "target": payload.target}

@router.get("/outbound", summary="List outbound relations from an entity")
def outbound(name: str = Query(...), svc = Depends(get_memory_service)):
    return {"source": name, "outbound": svc.associative.get_outbound(name)}

@router.get("/inbound", summary="List inbound relations to an entity")
def inbound(name: str = Query(...), svc = Depends(get_memory_service)):
    return {"target": name, "inbound": svc.associative.get_inbound(name)}

@router.get("/path", summary="Find a shortest path between two entities")
def path(a: str = Query(...), b: str = Query(...), max_hops: int = Query(4, ge=1, le=6), svc = Depends(get_memory_service)):
    return {"a": a, "b": b, "paths": svc.associative.path_between(a, b, max_hops)}

# ----------- Long-term storage endpoints  -----------
@router.post("/semantic")
async def add_semantic(m: SemanticCreate, svc: MemoryService = Depends(get_memory_service)):
    return {"id": await svc.add_semantic(m)}

@router.post("/episodic/conversational")
async def add_ep_conversational(m: EpisodicConversationalCreate, svc: MemoryService = Depends(get_memory_service)):
    return {"id": await svc.add_ep_conversational(m)}

@router.post("/episodic/summaries")
async def add_ep_summary(m: EpisodicSummaryCreate, svc: MemoryService = Depends(get_memory_service)):
    return {"id": await svc.add_ep_summary(m)}

@router.post("/episodic/observations")
async def add_ep_observation(m: EpisodicObservationCreate, svc: MemoryService = Depends(get_memory_service)):
    return {"id": await svc.add_ep_observation(m)}

@router.post("/procedural/agent")
async def add_proc_agent(m: ProceduralAgentCreate, svc: MemoryService = Depends(get_memory_service)):
    return {"id": await svc.add_proc_agent(m)}

@router.post("/procedural/tool")
async def add_proc_tool(m: ProceduralToolCreate, svc: MemoryService = Depends(get_memory_service)):
    return {"id": await svc.add_proc_tool(m)}

@router.post("/procedural/workflow")
async def add_proc_workflow(m: ProceduralWorkflowCreate, svc: MemoryService = Depends(get_memory_service)):
    return {"id": await svc.add_proc_workflow(m)}
