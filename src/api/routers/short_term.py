from fastapi import APIRouter, Depends
from ...memory.service import MemoryService
from ..deps import get_memory_service
from ...memory.types import RedisMemoryIn

router = APIRouter()

@router.post("/short-term/short")
async def add_short_term(
    m: RedisMemoryIn,
    svc: MemoryService = Depends(get_memory_service),
):
    assert m.memory_type == "short_term"
    return await svc.add_short_term(m)

@router.post("/short-term/working")
async def add_working(
    m: RedisMemoryIn,
    svc: MemoryService = Depends(get_memory_service),
):
    assert m.memory_type == "working"
    return await svc.add_working(m)
