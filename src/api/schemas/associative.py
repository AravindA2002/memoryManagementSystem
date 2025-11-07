
from typing import List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re

_REL_TYPE_REGEX = re.compile(r"^[A-Z][A-Z0-9_]*$")

class EntityIn(BaseModel):
    name: str = Field(..., description="Unique entity name")
    labels: List[str] = Field(default_factory=list, description="Additional labels (e.g., Person, Tool)")
    props: dict = Field(default_factory=dict, example={})

class RelationIn(BaseModel):
    source: str
    relation: str = Field(..., description="Relationship type, e.g., USES, BUILDS, FRIEND_OF")
    target: str
    props: dict = Field(default_factory=dict, example={})

    
    
