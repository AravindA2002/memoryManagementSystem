from __future__ import annotations
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
import time
import uuid

MemoryTypeStrict = Literal["short_term", "working", "long_term", "semantic"]

class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    memory_type: MemoryTypeStrict
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, str] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
