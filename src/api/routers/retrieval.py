from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from typing import Optional
from ...memory.service import MemoryService
from ...memory.types import ShortTermType, LongTermType
from ..deps import get_memory_service

router = APIRouter(prefix="/retrieve", tags=["retrieve"])

# Note: You can keep this file for backward compatibility or unified retrieval,
# but the main retrieval endpoints are now organized in short_term.py and long_term.py

@router.get("/", summary="Unified retrieval endpoint")
async def retrieve_unified(
    category: str = Query(..., description="'short-term' or 'long-term'"),
    memory_type: str = Query(..., description="Type of memory to retrieve"),
    agent_id: str = Query(..., description="Agent ID"),
    svc: MemoryService = Depends(get_memory_service),
):
    """
    Unified retrieval endpoint - consider using specific endpoints in /short-term or /long-term instead.
    This is kept for backward compatibility.
    """
    return {
        "message": "Please use specific endpoints:",
        "short_term": {
            "cache": "GET /short-term/cache",
            "working": "GET /short-term/working"
        },
        "long_term": {
            "semantic": "GET /long-term/semantic",
            "episodic": "GET /long-term/episodic",
            "procedural": "GET /long-term/procedural",
            "associative": "GET /long-term/associative"
        }
    }