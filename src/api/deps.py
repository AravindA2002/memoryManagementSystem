
from ..memory.service import MemoryService


_memory_service = MemoryService()

def get_memory_service() -> MemoryService:
    return _memory_service

