from __future__ import annotations
from typing import Literal, Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# -------------------- Enums --------------------
class ShortTermType(str, Enum):
    CACHE = "cache"
    WORKING = "working"

class LongTermType(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"

# ==================== SHORT TERM MEMORY SCHEMAS ====================

# -------------------- Base Schema --------------------
class ShortTermMemoryBase(BaseModel):
    """Base class for all short-term memories (common fields only)"""
    agent_id: str = Field(..., description="Agent ID (required)")
    memory: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs representing the memory content"
    )
    ttl: int = Field(default=600, description="Time to live in seconds (default: 600 = 10 mins)")
    message_id: Optional[str] = Field(default="", description="Auto-generated message ID")
    run_id: Optional[str] = Field(default="", description="Run ID for tracking")

# -------------------- Cache Memory Schema --------------------
class CacheMemory(ShortTermMemoryBase):
    """Cache memory schema - only base fields, no additional fields"""
    agent_id: str = Field(..., description="Agent ID (required)")
    memory: Dict[str, Any] = Field(..., description="Memory content")
    memory_type: Literal[ShortTermType.CACHE] = ShortTermType.CACHE
    ttl: int = Field(default=600, description="Time to live in seconds")
    message_id: Optional[str] = Field(default=None, description="Auto-generated")
    run_id: Optional[str] = Field(default="", description="Run ID")
# -------------------- Working Memory Schema --------------------
class WorkingMemory(ShortTermMemoryBase):
    """Working memory schema - base fields + workflow-specific fields"""
    memory_type: Literal[ShortTermType.WORKING] = ShortTermType.WORKING
    workflow_id: Optional[str] = Field(default=None, description="Workflow identifier")
    stages: List[str] = Field(default_factory=list, description="List of workflow stages")
    current_stage: Optional[str] = Field(default=None, description="Current stage in workflow")
    context_log_summary: Optional[str] = Field(default=None, description="Summary of context/logs")
    user_query: Optional[str] = Field(default=None, description="Original user query")

# -------------------- Working-persisted Memory Schema --------------------
class WorkingMemoryPersisted(BaseModel):
    """Persisted working memory - stored in MongoDB with exact same schema as short-term working memory"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: str = "working_persisted"
    message_id: str  # From short-term memory
    run_id: str = ""
    workflow_id: str = ""
    stages: List[str] = []
    current_stage: str = ""
    context_log_summary: str = ""
    user_query: str = ""
    created_at: str  # From short-term memory
    updated_at: Optional[str] = None  # From short-term memory if it was updated

# -------------------- Generic Schema (for backward compatibility) --------------------
class ShortTermMemory(ShortTermMemoryBase):
    """Generic short-term memory for API input (accepts both cache and working fields)"""
    memory_type: ShortTermType = Field(..., description="Type of short-term memory")
    workflow_id: Optional[str] = None
    stages: List[str] = Field(default_factory=list)
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None

# -------------------- Metadata Schema --------------------
class ShortTermMetadata(BaseModel):
    """Metadata for short-term memory responses"""
    created_at: str = Field(..., description="ISO format timestamp when memory was created")
    updated_at: Optional[str] = Field(default=None, description="ISO format timestamp when memory was last updated (only if updated)")

# -------------------- Output Schemas --------------------
class CacheMemoryOut(BaseModel):
    """Cache memory retrieval schema - clean, only cache-relevant fields"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["cache"] = "cache"
    ttl: int
    message_id: str
    run_id: Optional[str] = None
    metadata: ShortTermMetadata

class WorkingMemoryOut(BaseModel):
    """Working memory retrieval schema - includes workflow fields"""
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

# -------------------- Generic Output (for internal use) --------------------
class ShortTermMemoryOut(BaseModel):
    """Generic output model (for internal service layer)"""
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

# -------------------- Update Model --------------------
class ShortTermMemoryUpdate(BaseModel):
    """Model for updating short-term memory"""
    agent_id: str = Field(..., description="Agent ID (required for identification)")
    message_id: str = Field(..., description="Message ID (required for identification)")
    memory_type: ShortTermType = Field(..., description="Type of short-term memory")
    
    # Fields to update
    memory_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs to update or add in memory. Existing keys will be updated, new keys will be added."
    )
    remove_keys: List[str] = Field(
        default_factory=list,
        description="List of keys to remove from memory"
    )
    
    # Optional: Update other fields for working memory
    workflow_id: Optional[str] = Field(default=None)
    stages: Optional[List[str]] = Field(default=None)
    current_stage: Optional[str] = Field(default=None)
    context_log_summary: Optional[str] = Field(default=None)
    user_query: Optional[str] = Field(default=None)
    ttl: Optional[int] = Field(default=None, description="Update TTL (resets expiration)")
# ==================== LONG TERM MEMORY (Keep existing - will update later) ====================
class LongTermMemory(BaseModel):
    """Base class for all long-term memories (MongoDB-based, permanent)"""
    agent_id: str
    memory: Dict[str, Any] = Field(
        default_factory=dict,
        example={},
        description="Key-value pairs representing the memory content"
    )
    memory_type: LongTermType = Field(..., description="Type of long-term memory")
    message_id: Optional[str] = Field(default=None, description="Message ID for tracking")
    run_id: Optional[str] = Field(default=None, description="Run ID for tracking")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict, example={})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    source_system: Optional[str] = None
    version: int = 1
    deleted: bool = False
    
    # Semantic specific (only used when memory_type=SEMANTIC)
    normalized_text: Optional[str] = Field(default=None, description="Normalized text for embedding")
    
    # Subtype - different values for different memory types
    # For episodic: conversational, summaries, observations, working_persisted
    # For procedural: agent_store, tool_store, workflow_store
    subtype: Optional[str] = Field(default=None, description="Subtype varies by memory_type")
    
    # Episodic specific (only used when memory_type=EPISODIC)
    conversation_id: Optional[str] = None
    role: Optional[Literal["user","assistant","system"]] = None
    turn_index: Optional[int] = None
    channel: Optional[str] = None
    span_start: Optional[datetime] = None
    span_end: Optional[datetime] = None
    summary_type: Optional[Literal["extractive","abstractive"]] = None
    quality_score: Optional[float] = None
    observation_id: Optional[str] = None
    event: Optional[str] = None
    result: Optional[str] = None
    reward: Optional[float] = None
    credibility: Optional[float] = None
    source: Optional[str] = None
    
    # Working memory persisted fields (only used when subtype=working_persisted)
    workflow_id: Optional[str] = None
    stages: List[str] = Field(default_factory=list)
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None
    persisted_at: Optional[datetime] = None
    original_ttl: Optional[int] = None
    
    # Procedural specific (only used when memory_type=PROCEDURAL)
    name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    integration: Dict[str, Any] = Field(default_factory=dict)
    status: Optional[Literal["active","deprecated"]] = None
    change_note: Optional[str] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)

# -------------------- Update Models for Long Term --------------------
class LongTermMemoryUpdate(BaseModel):
    """Model for updating long-term memory"""
    agent_id: str = Field(..., description="Agent ID (required for identification)")
    message_id: str = Field(..., description="Message ID (required for identification)")
    memory_type: LongTermType = Field(..., description="Type of long-term memory")
    
    # Fields to update
    memory_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs to update or add in memory. Existing keys will be updated, new keys will be added."
    )
    remove_keys: List[str] = Field(
        default_factory=list,
        description="List of keys to remove from memory"
    )
    
    # Optional: Update metadata and other fields
    tags: Optional[List[str]] = None
    metadata_updates: Optional[Dict[str, Any]] = None
    
    # Optional: Update specific fields based on memory type
    normalized_text: Optional[str] = None  # For semantic
    subtype: Optional[str] = None  # For episodic/procedural
    conversation_id: Optional[str] = None
    workflow_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[Literal["active","deprecated"]] = None
    config_updates: Optional[Dict[str, Any]] = None  # For procedural