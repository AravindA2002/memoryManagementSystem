from __future__ import annotations
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime

# -------------------- Base --------------------
class BaseDoc(BaseModel):
    agent_id: str                          # partition key
    memory: str                            # the human-readable body
    memory_type: Literal["semantic","episodic","procedural","associative","short_term","working"]
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    source_system: Optional[str] = None
    version: int = 1
    deleted: bool = False

# -------------------- Short-lived (Redis) --------------------
RedisType = Literal["short_term","working"]

class RedisMemoryIn(BaseModel):
    agent_id: str
    memory: str
    ttl: int
    memory_type: RedisType

# Keep the alias so older imports don't break
RedisMemoryType = RedisType  # backward compatibility

from datetime import datetime

class RedisMemoryOut(RedisMemoryIn):
    id: str
    created_at: datetime


# -------------------- Semantic (Chroma) --------------------
class SemanticCreate(BaseDoc):
    memory_type: Literal["semantic"] = "semantic"
    normalized_text: Optional[str] = None
    # embeddings are produced via OpenAI on write and stored only in Chroma
    # keep here for traceability if you want to mirror
    embedding_model: Optional[str] = None
    embedding_dim: Optional[int] = None

# -------------------- Episodic (Mongo, append-only) --------------------
# sub-collections: conversational | summaries | observations
class EpisodicConversationalCreate(BaseDoc):
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["conversational"] = "conversational"
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    role: Optional[Literal["user","assistant","system"]] = None
    turn_index: Optional[int] = None
    channel: Optional[str] = None        # chat|voice|api
    run_id: Optional[str] = None

class EpisodicSummaryCreate(BaseDoc):
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["summaries"] = "summaries"
    conversation_id: Optional[str] = None
    span_start: Optional[datetime] = None
    span_end: Optional[datetime] = None
    summary_type: Optional[Literal["extractive","abstractive"]] = None
    quality_score: Optional[float] = None

class EpisodicObservationCreate(BaseDoc):
    memory_type: Literal["episodic"] = "episodic"
    subtype: Literal["observations"] = "observations"
    observation_id: Optional[str] = None
    event: Optional[str] = None
    result: Optional[str] = None
    reward: Optional[float] = None
    credibility: Optional[float] = None
    source: Optional[str] = None

# -------------------- Procedural (Mongo) --------------------
# sub-collections: agent_store | tool_store | workflow_store
class ProceduralAgentCreate(BaseDoc):
    memory_type: Literal["procedural"] = "procedural"
    subtype: Literal["agent_store"] = "agent_store"
    name: str
    config: Dict[str, object] = Field(default_factory=dict)
    status: Literal["active","deprecated"] = "active"
    change_note: Optional[str] = None

class ProceduralToolCreate(BaseDoc):
    memory_type: Literal["procedural"] = "procedural"
    subtype: Literal["tool_store"] = "tool_store"
    name: str
    config: Dict[str, object] = Field(default_factory=dict)
    integration: Dict[str, object] = Field(default_factory=dict)
    status: Literal["active","deprecated"] = "active"

class ProceduralWorkflowCreate(BaseDoc):
    memory_type: Literal["procedural"] = "procedural"
    subtype: Literal["workflow_store"] = "workflow_store"
    name: str
    steps: List[Dict[str, object]] = Field(default_factory=list)
    integration: Dict[str, object] = Field(default_factory=dict)
    status: Literal["active","deprecated"] = "active"
