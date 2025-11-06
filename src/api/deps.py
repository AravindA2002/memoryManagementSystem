# src/api/deps.py
from ..memory.service import MemoryService

# Single, shared instance for the process
_memory_service = MemoryService()

def get_memory_service() -> MemoryService:
    return _memory_service

