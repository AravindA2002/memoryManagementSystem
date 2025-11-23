from __future__ import annotations
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Enums
class ShortTermType(str, Enum):
    CACHE = "cache"
    WORKING = "working"

class LongTermType(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    SEMANTIC_SUPERMEMORY = "semantic_supermemory"  # NEW
    WORKING_PERSISTED = "working_persisted"

class EpisodicSubtype(str, Enum):
    CONVERSATIONAL = "conversational"
    SUMMARIES = "summaries"
    OBSERVATIONS = "observations"

# SHORT TERM MEMORY INPUT SCHEMAS

class ShortTermMemoryBase(BaseModel):
    """Base for short-term memories"""
    agent_id: str = Field(..., description="Agent ID")
    memory: Dict[str, Any] = Field(default_factory=dict, description="Memory content")
    ttl: int = Field(default=600, description="TTL in seconds")
    message_id: Optional[str] = Field(default="", description="Auto-generated")
    run_id: Optional[str] = Field(default="", description="Run ID")

class CacheMemory(ShortTermMemoryBase):
    """Cache memory input schema"""
    memory_type: Literal[ShortTermType.CACHE] = ShortTermType.CACHE

class WorkingMemory(ShortTermMemoryBase):
    """Working memory input schema"""
    memory_type: Literal[ShortTermType.WORKING] = ShortTermType.WORKING
    workflow_id: Optional[str] = None
    stages: List[str] = Field(default_factory=list)
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None

class ShortTermMemory(ShortTermMemoryBase):
    """Generic short-term memory for internal use"""
    memory_type: ShortTermType
    workflow_id: Optional[str] = None
    stages: List[str] = Field(default_factory=list)
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None

# SHORT TERM MEMORY OUTPUT SCHEMAS

class ShortTermMetadata(BaseModel):
    """Metadata for responses"""
    created_at: str
    updated_at: Optional[str] = None

class CacheMemoryOut(BaseModel):
    """Cache output schema"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["cache"] = "cache"
    ttl: int
    message_id: str
    run_id: Optional[str] = None
    metadata: ShortTermMetadata

class WorkingMemoryOut(BaseModel):
    """Working output schema"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["working"] = "working"
    ttl: int
    message_id: str
    run_id: Optional[str] = None
    workflow_id: Optional[str] = None
    stages: List[str] = Field(default_factory=list)
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None
    metadata: ShortTermMetadata

class ShortTermMemoryOut(BaseModel):
    """Internal output model for service layer"""
    id: str
    agent_id: str
    memory: Dict[str, Any]
    memory_type: ShortTermType
    ttl: int
    message_id: str
    run_id: Optional[str] = None
    workflow_id: Optional[str] = None
    stages: List[str] = Field(default_factory=list)
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# SHORT TERM MEMORY UPDATE SCHEMAS

class ShortTermMemoryUpdate(BaseModel):
    """Update model for short-term memory"""
    agent_id: str
    message_id: str
    memory_type: ShortTermType
    memory_updates: Dict[str, Any] = Field(default_factory=dict)
    remove_keys: List[str] = Field(default_factory=list)
    workflow_id: Optional[str] = None
    stages: Optional[List[str]] = None
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None
    ttl: Optional[int] = None

# LONG TERM MEMORY INPUT SCHEMAS

class LongTermMemoryBase(BaseModel):
    """Base for long-term memories"""
    agent_id: str
    memory: Dict[str, Any]
    message_id: Optional[str] = Field(default="", description="Auto-generated")
    run_id: Optional[str] = None

class ConversationalMemory(LongTermMemoryBase):
    """Conversational episodic memory input schema"""
    memory_type: Literal[LongTermType.EPISODIC] = LongTermType.EPISODIC
    subtype: Literal["conversational"] = Field(default="conversational")
    conversation_id: str
    role: str
    current_stage: Optional[str] = ""
    recall_recovery: Optional[str] = ""
    embeddings: List[float] = Field(default_factory=list)

class SummariesMemory(LongTermMemoryBase):
    """Summaries episodic memory input schema"""
    memory_type: Literal[LongTermType.EPISODIC] = LongTermType.EPISODIC
    subtype: Literal["summaries"] = Field(default="summaries")

class ObservationsMemory(LongTermMemoryBase):
    """Observations episodic memory input schema"""
    memory_type: Literal[LongTermType.EPISODIC] = LongTermType.EPISODIC
    subtype: Literal["observations"] = Field(default="observations")
    observation_id: str
    observation_kpi: Optional[str] = ""
    recall_recovery: Optional[str] = ""
    embeddings: List[float] = Field(default_factory=list)

class SemanticMemory(LongTermMemoryBase):
    """Semantic memory input schema"""
    memory_type: Literal[LongTermType.SEMANTIC] = LongTermType.SEMANTIC
    normalized_text: Optional[str] = None

class ProceduralMemory(LongTermMemoryBase):
    """Procedural memory input schema"""
    memory_type: Literal[LongTermType.PROCEDURAL] = LongTermType.PROCEDURAL
    subtype: Literal["agent_store", "tool_store", "workflow_store"]
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    integration: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["active", "deprecated"] = Field(default="active")
    change_note: Optional[str] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)

class WorkingMemoryPersisted(BaseModel):
    """Persisted working memory input/storage schema"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["working_persisted"] = "working_persisted"
    message_id: str
    run_id: Optional[str] = ""
    workflow_id: Optional[str] = None
    stages: List[str] = Field(default_factory=list)
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    persisted_at: datetime = Field(default_factory=datetime.utcnow)
    original_ttl: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    version: int = Field(default=1)

# LONG TERM MEMORY OUTPUT SCHEMAS

class LongTermMetadataOut(BaseModel):
    """Metadata for long-term memory output"""
    created_at: str
    updated_at: Optional[str] = None

class SemanticMemoryOut(BaseModel):
    """Semantic memory output schema"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["semantic"] = "semantic"
    message_id: str
    run_id: Optional[str] = None
    metadata: LongTermMetadataOut

class ConversationalMemoryOut(BaseModel):
    """Conversational episodic output schema"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["conversational"] = "conversational"
    message_id: str
    run_id: Optional[str] = None
    conversation_id: str
    role: str
    current_stage: Optional[str] = None
    recall_recovery: Optional[str] = None
    embeddings: List[float] = Field(default_factory=list)
    metadata: LongTermMetadataOut

class SummariesMemoryOut(BaseModel):
    """Summaries episodic output schema"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["summaries"] = "summaries"
    message_id: str
    run_id: Optional[str] = None
    metadata: LongTermMetadataOut

class ObservationsMemoryOut(BaseModel):
    """Observations episodic output schema"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["observations"] = "observations"
    message_id: str
    run_id: Optional[str] = None
    observation_id: str
    observation_kpi: Optional[str] = None
    recall_recovery: Optional[str] = None
    embeddings: List[float] = Field(default_factory=list)
    metadata: LongTermMetadataOut

class ProceduralMemoryOut(BaseModel):
    """Procedural memory output schema"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["procedural"] = "procedural"
    subtype: str
    message_id: str
    run_id: Optional[str] = None
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    integration: Dict[str, Any] = Field(default_factory=dict)
    status: Optional[str] = None
    change_note: Optional[str] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: LongTermMetadataOut

class WorkingMemoryPersistedOut(BaseModel):
    """Working persisted memory output schema"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["working_persisted"] = "working_persisted"
    message_id: str
    run_id: Optional[str] = None
    workflow_id: Optional[str] = None
    stages: List[str] = Field(default_factory=list)
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

# LONG TERM MEMORY UPDATE SCHEMAS

class SemanticMemoryUpdate(BaseModel):
    """Semantic memory update schema"""
    agent_id: str
    message_id: str
    memory_updates: Dict[str, Any] = Field(default_factory=dict)
    remove_keys: List[str] = Field(default_factory=list)
    normalized_text: Optional[str] = None

class ProceduralMemoryUpdate(BaseModel):
    """Procedural memory update schema"""
    agent_id: str
    message_id: str
    memory_updates: Dict[str, Any] = Field(default_factory=dict)
    remove_keys: List[str] = Field(default_factory=list)
    subtype: Optional[Literal["agent_store", "tool_store", "workflow_store"]] = None
    name: Optional[str] = None
    config_updates: Optional[Dict[str, Any]] = None
    integration_updates: Optional[Dict[str, Any]] = None
    status: Optional[Literal["active", "deprecated"]] = None
    change_note: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None

class WorkingMemoryPersistedUpdate(BaseModel):
    """Working persisted memory update schema"""
    agent_id: str
    message_id: str
    memory_updates: Dict[str, Any] = Field(default_factory=dict)
    remove_keys: List[str] = Field(default_factory=list)
    workflow_id: Optional[str] = None
    stages: Optional[List[str]] = None
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None
    tags: Optional[List[str]] = None



# INTERNAL STORAGE SCHEMAS (for MongoDB/Redis storage layer only)

# Add after the internal storage schemas section

# INTERNAL STORAGE SCHEMAS - CLEAN (MongoDB specific)

class SemanticMemoryStorage(BaseModel):
    """Clean storage for semantic memory in MongoDB"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["semantic"] = "semantic"
    message_id: str
    run_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    normalized_text: Optional[str] = None
    version: int = Field(default=1)

# Add this after SemanticMemory class

class SupermemorySemanticMemory(LongTermMemoryBase):
    """Supermemory semantic memory input schema"""
    memory_type: Literal["semantic_supermemory"] = "semantic_supermemory"
    content: str = Field(..., description="Text content to store in Supermemory")
    spaces: List[str] = Field(default_factory=list, description="Space IDs to add memory to")
    metadata_extra: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

# Add to LongTermType enum


class ConversationalMemoryStorage(BaseModel):
    """Clean storage for conversational episodic memory in MongoDB"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["conversational"] = "conversational"
    message_id: str
    run_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    conversation_id: str
    role: str
    current_stage: Optional[str] = None
    recall_recovery: Optional[str] = None
    embeddings: List[float] = Field(default_factory=list)
    version: int = Field(default=1)

class SummariesMemoryStorage(BaseModel):
    """Clean storage for summaries episodic memory in MongoDB"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["summaries"] = "summaries"
    message_id: str
    run_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    version: int = Field(default=1)

class ObservationsMemoryStorage(BaseModel):
    """Clean storage for observations episodic memory in MongoDB"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["observations"] = "observations"
    message_id: str
    run_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    observation_id: str
    observation_kpi: Optional[str] = None
    recall_recovery: Optional[str] = None
    embeddings: List[float] = Field(default_factory=list)
    version: int = Field(default=1)

class ProceduralMemoryStorage(BaseModel):
    """Clean storage for procedural memory in MongoDB"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["procedural"] = "procedural"
    subtype: str
    message_id: str
    run_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    integration: Dict[str, Any] = Field(default_factory=dict)
    status: Optional[Literal["active", "deprecated"]] = None
    change_note: Optional[str] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    version: int = Field(default=1)


class LongTermMemoryUpdateStorage(BaseModel):
    """Internal update model for MongoDB operations"""
    agent_id: str
    message_id: str
    memory_type: LongTermType
    memory_updates: Dict[str, Any] = Field(default_factory=dict)
    remove_keys: List[str] = Field(default_factory=list)
    
    # Optional fields for different memory types
    normalized_text: Optional[str] = None
    subtype: Optional[str] = None
    conversation_id: Optional[str] = None
    role: Optional[str] = None
    current_stage: Optional[str] = None
    recall_recovery: Optional[str] = None
    embeddings: Optional[List[float]] = None
    observation_id: Optional[str] = None
    observation_kpi: Optional[str] = None
    name: Optional[str] = None
    config_updates: Optional[Dict[str, Any]] = None
    integration_updates: Optional[Dict[str, Any]] = None
    status: Optional[Literal["active", "deprecated"]] = None
    change_note: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None

