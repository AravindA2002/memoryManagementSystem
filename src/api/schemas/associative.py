# src/api/schemas/associative.py
from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re

_REL_TYPE_REGEX = re.compile(r"^[A-Z][A-Z0-9_]*$")

class EntityIn(BaseModel):
    name: str = Field(..., description="Unique entity name")
    labels: List[str] = Field(default_factory=list, description="Additional labels (e.g., Person, Tool)")
    props: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")

class RelationIn(BaseModel):
    source: str
    relation: str = Field(..., description="Relationship type, e.g., USES, BUILDS, FRIEND_OF")
    target: str
    props: Dict[str, Any] = Field(default_factory=dict)

    # Normalize and validate relation here (keeps router super clean)
    @field_validator("relation")
    @classmethod
    def normalize_relation(cls, v: str) -> str:
        rel = (v or "").strip().upper().replace(" ", "_")
        if not _REL_TYPE_REGEX.fullmatch(rel):
            raise ValueError(
                "relation must match ^[A-Z][A-Z0-9_]*$ (upper-case, underscores, start with letter)"
            )
        return rel
