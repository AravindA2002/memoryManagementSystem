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
    WORKING_PERSISTED = "working_persisted"

class EpisodicSubtype(str, Enum):
    CONVERSATIONAL = "conversational"
    SUMMARIES = "summaries"
    OBSERVATIONS = "observations"

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
    """
    Persisted working memory - stored in MongoDB with exact same schema as short-term working memory.
    This is stored in its OWN collection (lt_working_persisted), NOT under episodic.
    """
    agent_id: str = Field(..., description="Agent ID (required)")
    memory: Dict[str, Any] = Field(..., description="Memory content - same as short-term")
    memory_type: Literal["working_persisted"] = "working_persisted"
    message_id: str = Field(..., description="Message ID from short-term memory")
    run_id: Optional[str] = Field(default="", description="Run ID for tracking")
    
    # Working memory specific fields (same as WorkingMemory)
    workflow_id: Optional[str] = Field(default=None, description="Workflow identifier")
    stages: List[str] = Field(default_factory=list, description="List of workflow stages")
    current_stage: Optional[str] = Field(default=None, description="Current stage in workflow")
    context_log_summary: Optional[str] = Field(default=None, description="Summary of context/logs")
    user_query: Optional[str] = Field(default=None, description="Original user query")
    
    # Metadata fields
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When it was originally created in short-term")
    updated_at: Optional[datetime] = Field(default=None, description="When it was last updated in short-term (only if updated)")
    persisted_at: datetime = Field(default_factory=datetime.utcnow, description="When it was persisted to long-term")
    original_ttl: Optional[int] = Field(default=None, description="Original TTL from short-term memory")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    version: int = Field(default=1, description="Version number for updates")

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

# ==================== LONG TERM MEMORY SCHEMAS (CLEANED) ====================

# -------------------- Base Long Term Schema --------------------
class LongTermMemoryBase(BaseModel):
    """Base schema for all long-term memories"""
    agent_id: str = Field(..., description="Agent ID (required)")
    memory: Dict[str, Any] = Field(..., description="Memory content")
    message_id: Optional[str] = Field(default="", description="Auto-generated message ID")
    run_id: Optional[str] = Field(default=None, description="Run ID for tracking")

# ==================== EPISODIC MEMORY SCHEMAS ====================

# -------------------- Conversational Schema --------------------
class ConversationalMemory(LongTermMemoryBase):
    """Conversational episodic memory - for chat/dialogue interactions"""
    memory_type: Literal[LongTermType.EPISODIC] = LongTermType.EPISODIC
    subtype: Literal["conversational"] = Field(default="conversational", description="Auto-set to conversational")
    message_id: Optional[str] = Field(default="", description="Auto-generated")
    conversation_id: str = Field(..., description="Conversation identifier")
    role: str = Field(..., description="Role (user/assistant/system)")
    current_stage: Optional[str] = Field(default="", description="Current conversation stage")
    recall_recovery: Optional[str] = Field(default="", description="Recall recovery information")
    embeddings: List[float] = Field(default_factory=list, description="Vector embeddings")

# -------------------- Summaries Schema --------------------
class SummariesMemory(LongTermMemoryBase):
    """Summaries episodic memory - just base schema, nothing extra"""
    memory_type: Literal[LongTermType.EPISODIC] = LongTermType.EPISODIC
    subtype: Literal["summaries"] = Field(default="summaries", description="Auto-set to summaries")
    message_id: Optional[str] = Field(default="", description="Auto-generated")

# -------------------- Observations Schema --------------------
class ObservationsMemory(LongTermMemoryBase):
    """Observations episodic memory - for agent observations and learnings"""
    memory_type: Literal[LongTermType.EPISODIC] = LongTermType.EPISODIC
    subtype: Literal["observations"] = Field(default="observations", description="Auto-set to observations")
    message_id: Optional[str] = Field(default="", description="Auto-generated")
    observation_id: str = Field(..., description="Observation identifier")
    observation_kpi: Optional[str] = Field(default="", description="Observation KPI metrics")
    recall_recovery: Optional[str] = Field(default="", description="Recall recovery information")
    embeddings: List[float] = Field(default_factory=list, description="Vector embeddings")
# -------------------- Generic Episodic (for backward compatibility) --------------------
class EpisodicMemory(BaseModel):
    """Generic episodic memory input (accepts all subtypes)"""
    agent_id: str = Field(..., description="Agent ID (required)")
    memory: Dict[str, Any] = Field(..., description="Memory content")
    memory_type: Literal[LongTermType.EPISODIC] = LongTermType.EPISODIC
    message_id: Optional[str] = Field(default="", description="Auto-generated")
    run_id: Optional[str] = Field(default="", description="Run ID")
    subtype: Literal["conversational", "summaries", "observations"] = Field(..., description="Episodic subtype")
    
    # Conversational fields
    conversation_id: Optional[str] = None
    role: Optional[str] = None
    current_stage: Optional[str] = None
    recall_recovery: Optional[str] = None
    embeddings: List[float] = Field(default_factory=list)
    
    # Observations fields
    observation_id: Optional[str] = None
    observation_kpi: Optional[str] = None

# ==================== LONG TERM OUTPUT SCHEMAS ====================

# -------------------- Metadata Output Schema --------------------
class LongTermMetadataOut(BaseModel):
    """Metadata for long-term memory responses"""
    created_at: str = Field(..., description="When memory was created (format: DD-MM-YYYY HH:MM)")
    updated_at: Optional[str] = Field(default=None, description="When memory was last updated (only if updated)")

# -------------------- Semantic Output Schema --------------------
class SemanticMemoryOut(BaseModel):
    """Output schema for semantic memory retrieval"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["semantic"] = "semantic"
    message_id: str
    run_id: Optional[str] = None
    metadata: LongTermMetadataOut

# -------------------- Episodic Output Schemas --------------------

class ConversationalMemoryOut(BaseModel):
    """Output schema for conversational episodic memory"""
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
    """Output schema for summaries episodic memory"""
    agent_id: str
    memory: Dict[str, Any]
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["summaries"] = "summaries"
    message_id: str
    run_id: Optional[str] = None
    metadata: LongTermMetadataOut

class ObservationsMemoryOut(BaseModel):
    """Output schema for observations episodic memory"""
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

# ==================== SEMANTIC MEMORY SCHEMA ====================

class SemanticMemory(LongTermMemoryBase):
    """Semantic memory - just base schema, nothing extra"""
    memory_type: Literal[LongTermType.SEMANTIC] = LongTermType.SEMANTIC
    message_id: Optional[str] = Field(default="", description="Auto-generated")
    normalized_text: Optional[str] = Field(default=None, description="Normalized text for embedding (internal use)")

# ==================== PROCEDURAL MEMORY SCHEMA ====================

class ProceduralMemory(LongTermMemoryBase):
    """Procedural memory - for agent/tool/workflow configurations"""
    memory_type: Literal[LongTermType.PROCEDURAL] = LongTermType.PROCEDURAL
    message_id: Optional[str] = Field(default="", description="Auto-generated")
    subtype: Literal["agent_store", "tool_store", "workflow_store"] = Field(..., description="Procedural subtype")
    name: str = Field(..., description="Name of the procedure/config")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration data")
    integration: Dict[str, Any] = Field(default_factory=dict, description="Integration details")
    status: Literal["active", "deprecated"] = Field(default="active", description="Status")
    change_note: Optional[str] = Field(default=None, description="Change notes")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Procedure steps")

# ==================== LONG TERM UPDATE SCHEMAS ====================

# -------------------- Episodic Update (Conversational) --------------------
class ConversationalMemoryUpdate(BaseModel):
    """Update schema for conversational episodic memory"""
    agent_id: str = Field(..., description="Agent ID (required)")
    message_id: str = Field(..., description="Message ID (required)")
    
    # Fields to update
    memory_updates: Dict[str, Any] = Field(default_factory=dict, description="Memory updates")
    remove_keys: List[str] = Field(default_factory=list, description="Keys to remove")
    
    # Conversational specific updates
    conversation_id: Optional[str] = None
    role: Optional[str] = None
    current_stage: Optional[str] = None
    recall_recovery: Optional[str] = None
    embeddings: Optional[List[float]] = None

# -------------------- Episodic Update (Summaries) --------------------
class SummariesMemoryUpdate(BaseModel):
    """Update schema for summaries episodic memory"""
    agent_id: str = Field(..., description="Agent ID (required)")
    message_id: str = Field(..., description="Message ID (required)")
    
    # Fields to update
    memory_updates: Dict[str, Any] = Field(default_factory=dict, description="Memory updates")
    remove_keys: List[str] = Field(default_factory=list, description="Keys to remove")

# -------------------- Episodic Update (Observations) --------------------
class ObservationsMemoryUpdate(BaseModel):
    """Update schema for observations episodic memory"""
    agent_id: str = Field(..., description="Agent ID (required)")
    message_id: str = Field(..., description="Message ID (required)")
    
    # Fields to update
    memory_updates: Dict[str, Any] = Field(default_factory=dict, description="Memory updates")
    remove_keys: List[str] = Field(default_factory=list, description="Keys to remove")
    
    # Observations specific updates
    observation_id: Optional[str] = None
    observation_kpi: Optional[str] = None
    recall_recovery: Optional[str] = None
    embeddings: Optional[List[float]] = None

# -------------------- Semantic Update --------------------
class SemanticMemoryUpdate(BaseModel):
    """Update schema for semantic memory"""
    agent_id: str = Field(..., description="Agent ID (required)")
    message_id: str = Field(..., description="Message ID (required)")
    
    # Fields to update
    memory_updates: Dict[str, Any] = Field(default_factory=dict, description="Memory updates")
    remove_keys: List[str] = Field(default_factory=list, description="Keys to remove")
    normalized_text: Optional[str] = None

# -------------------- Procedural Update --------------------
class ProceduralMemoryUpdate(BaseModel):
    """Update schema for procedural memory"""
    agent_id: str = Field(..., description="Agent ID (required)")
    message_id: str = Field(..., description="Message ID (required)")
    
    # Fields to update
    memory_updates: Dict[str, Any] = Field(default_factory=dict, description="Memory updates")
    remove_keys: List[str] = Field(default_factory=list, description="Keys to remove")
    
    # Procedural specific updates
    subtype: Optional[Literal["agent_store", "tool_store", "workflow_store"]] = None
    name: Optional[str] = None
    config_updates: Optional[Dict[str, Any]] = None
    integration_updates: Optional[Dict[str, Any]] = None
    status: Optional[Literal["active", "deprecated"]] = None
    change_note: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None

# -------------------- Working Persisted Update --------------------
class WorkingMemoryPersistedUpdate(BaseModel):
    """Update schema for working_persisted memory"""
    agent_id: str = Field(..., description="Agent ID (required)")
    message_id: str = Field(..., description="Message ID (required)")
    
    # Fields to update
    memory_updates: Dict[str, Any] = Field(default_factory=dict)
    remove_keys: List[str] = Field(default_factory=list)
    
    # Optional: Update working memory specific fields
    workflow_id: Optional[str] = None
    stages: Optional[List[str]] = None
    current_stage: Optional[str] = None
    context_log_summary: Optional[str] = None
    user_query: Optional[str] = None
    tags: Optional[List[str]] = None

# ==================== LEGACY SUPPORT (for backward compatibility) ====================

class LongTermMemory(BaseModel):
    """Legacy generic long-term memory model (for backward compatibility)"""
    agent_id: str
    memory: Dict[str, Any] = Field(default_factory=dict)
    memory_type: LongTermType = Field(..., description="Type of long-term memory")
    message_id: Optional[str] = Field(default="", description="Auto-generated")
    run_id: Optional[str] = Field(default="", description="Run ID")
    
    # Metadata (auto-generated, not editable by user)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Semantic specific
    normalized_text: Optional[str] = None
    
    # Episodic specific
    subtype: Optional[str] = None
    conversation_id: Optional[str] = None
    role: Optional[str] = None
    current_stage: Optional[str] = None
    recall_recovery: Optional[str] = None
    embeddings: List[float] = Field(default_factory=list)
    observation_id: Optional[str] = None
    observation_kpi: Optional[str] = None
    
    # Procedural specific
    name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    integration: Dict[str, Any] = Field(default_factory=dict)
    status: Optional[Literal["active", "deprecated"]] = None
    change_note: Optional[str] = None
    steps: List[Dict[str, Any]] = Field(default_factory=list)

class LongTermMemoryUpdate(BaseModel):
    """Legacy generic update model"""
    agent_id: str = Field(..., description="Agent ID (required)")
    message_id: str = Field(..., description="Message ID (required)")
    memory_type: LongTermType = Field(..., description="Type of long-term memory")
    
    memory_updates: Dict[str, Any] = Field(default_factory=dict)
    remove_keys: List[str] = Field(default_factory=list)
    
    # Optional fields for different types
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