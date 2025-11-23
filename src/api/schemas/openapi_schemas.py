"""
OpenAPI schema definitions for Swagger UI documentation.
Keeps router files clean by separating API documentation.
"""

# ==================== SHORT TERM - CACHE ====================

CACHE_POST_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "CacheMemory",
                    "type": "object",
                    "required": ["agent_id", "memory"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "memory": {
                            "type": "object",
                            "title": "Memory",
                            "default": {}
                        },
                        "memory_type": {
                            "type": "string",
                            "title": "Memory Type",
                            "default": "cache"
                        },
                        "ttl": {
                            "type": "integer",
                            "title": "Ttl",
                            "default": 600
                        },
                        "run_id": {
                            "type": "string",
                            "title": "Run Id",
                            "default": ""
                        }
                    }
                }
            }
        }
    }
}

CACHE_PATCH_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "ShortTermMemoryUpdate",
                    "type": "object",
                    "required": ["agent_id", "message_id", "memory_type"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "message_id": {
                            "type": "string",
                            "title": "Message Id",
                            "default": ""
                        },
                        "memory_type": {
                            "type": "string",
                            "title": "Memory Type",
                            "default": "cache"
                        },
                        "memory_updates": {
                            "type": "object",
                            "title": "Memory Updates",
                            "default": {}
                        },
                        "remove_keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Remove Keys",
                            "default": []
                        },
                        "ttl": {
                            "type": "integer",
                            "title": "Ttl",
                            "default": 0
                        }
                    }
                }
            }
        }
    }
}

# ==================== SHORT TERM - WORKING ====================

WORKING_POST_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "WorkingMemory",
                    "type": "object",
                    "required": ["agent_id", "memory"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "memory": {
                            "type": "object",
                            "title": "Memory",
                            "default": {}
                        },
                        "memory_type": {
                            "type": "string",
                            "title": "Memory Type",
                            "default": "working"
                        },
                        "ttl": {
                            "type": "integer",
                            "title": "Ttl",
                            "default": 600
                        },
                        "run_id": {
                            "type": "string",
                            "title": "Run Id",
                            "default": ""
                        },
                        "workflow_id": {
                            "type": "string",
                            "title": "Workflow Id",
                            "default": ""
                        },
                        "stages": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Stages",
                            "default": []
                        },
                        "current_stage": {
                            "type": "string",
                            "title": "Current Stage",
                            "default": ""
                        },
                        "context_log_summary": {
                            "type": "string",
                            "title": "Context Log Summary",
                            "default": ""
                        },
                        "user_query": {
                            "type": "string",
                            "title": "User Query",
                            "default": ""
                        }
                    }
                }
            }
        }
    }
}

WORKING_PATCH_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "ShortTermMemoryUpdate",
                    "type": "object",
                    "required": ["agent_id", "message_id", "memory_type"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "message_id": {
                            "type": "string",
                            "title": "Message Id",
                            "default": ""
                        },
                        "memory_type": {
                            "type": "string",
                            "title": "Memory Type",
                            "default": "working"
                        },
                        "memory_updates": {
                            "type": "object",
                            "title": "Memory Updates",
                            "default": {}
                        },
                        "remove_keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Remove Keys",
                            "default": []
                        },
                        "workflow_id": {
                            "type": "string",
                            "title": "Workflow Id",
                            "default": ""
                        },
                        "stages": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Stages",
                            "default": []
                        },
                        "current_stage": {
                            "type": "string",
                            "title": "Current Stage",
                            "default": ""
                        },
                        "context_log_summary": {
                            "type": "string",
                            "title": "Context Log Summary",
                            "default": ""
                        },
                        "user_query": {
                            "type": "string",
                            "title": "User Query",
                            "default": ""
                        },
                        "ttl": {
                            "type": "integer",
                            "title": "Ttl",
                            "default": 0
                        }
                    }
                }
            }
        }
    }
}

# ==================== LONG TERM - SEMANTIC ====================

SEMANTIC_POST_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "SemanticMemory",
                    "type": "object",
                    "required": ["agent_id", "memory"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "memory": {
                            "type": "object",
                            "title": "Memory",
                            "default": {}
                        },
                        "run_id": {
                            "type": "string",
                            "title": "Run Id",
                            "default": ""
                        }
                    },
                    "description": "Note: message_id and memory_type are auto-generated"
                }
            }
        }
    }
}

SEMANTIC_PATCH_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "SemanticMemoryUpdate",
                    "type": "object",
                    "required": ["agent_id", "message_id"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "message_id": {
                            "type": "string",
                            "title": "Message Id",
                            "default": ""
                        },
                        "memory_updates": {
                            "type": "object",
                            "title": "Memory Updates",
                            "default": {}
                        },
                        "remove_keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Remove Keys",
                            "default": []
                        },
                        "normalized_text": {
                            "type": "string",
                            "title": "Normalized Text",
                            "default": ""
                        }
                    },
                    "description": "Note: memory_type is automatically set to 'semantic'"
                }
            }
        }
    }
}

# ==================== LONG TERM - EPISODIC (CONVERSATIONAL) ====================

EPISODIC_CONVERSATIONAL_POST_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "ConversationalMemory",
                    "type": "object",
                    "required": ["agent_id", "memory", "conversation_id", "role"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "memory": {
                            "type": "object",
                            "title": "Memory",
                            "default": {}
                        },
                        "run_id": {
                            "type": "string",
                            "title": "Run Id",
                            "default": ""
                        },
                        "conversation_id": {
                            "type": "string",
                            "title": "Conversation Id",
                            "default": "",
                            "description": "Conversation identifier (required)"
                        },
                        "role": {
                            "type": "string",
                            "title": "Role",
                            "default": "",
                            "description": "Role: user/assistant/system (required)"
                        },
                        "current_stage": {
                            "type": "string",
                            "title": "Current Stage",
                            "default": "",
                            "description": "Current conversation stage"
                        },
                        "recall_recovery": {
                            "type": "string",
                            "title": "Recall Recovery",
                            "default": "",
                            "description": "Recall recovery information"
                        },
                        "embeddings": {
                            "type": "array",
                            "items": {"type": "number"},
                            "title": "Embeddings",
                            "default": [],
                            "description": "Vector embeddings"
                        }
                    },
                    "description": "Note: message_id, memory_type, and subtype are auto-generated/auto-set"
                }
            }
        }
    }
}

# ==================== LONG TERM - EPISODIC (SUMMARIES) ====================

EPISODIC_SUMMARIES_POST_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "SummariesMemory",
                    "type": "object",
                    "required": ["agent_id", "memory"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "memory": {
                            "type": "object",
                            "title": "Memory",
                            "default": {}
                        },
                        "run_id": {
                            "type": "string",
                            "title": "Run Id",
                            "default": ""
                        }
                    },
                    "description": "Note: message_id, memory_type, and subtype are auto-generated/auto-set"
                }
            }
        }
    }
}

# ==================== LONG TERM - EPISODIC (OBSERVATIONS) ====================

EPISODIC_OBSERVATIONS_POST_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "ObservationsMemory",
                    "type": "object",
                    "required": ["agent_id", "memory", "observation_id"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "memory": {
                            "type": "object",
                            "title": "Memory",
                            "default": {}
                        },
                        "run_id": {
                            "type": "string",
                            "title": "Run Id",
                            "default": ""
                        },
                        "observation_id": {
                            "type": "string",
                            "title": "Observation Id",
                            "default": "",
                            "description": "Observation identifier (required)"
                        },
                        "observation_kpi": {
                            "type": "string",
                            "title": "Observation KPI",
                            "default": "",
                            "description": "Observation KPI metrics"
                        },
                        "recall_recovery": {
                            "type": "string",
                            "title": "Recall Recovery",
                            "default": "",
                            "description": "Recall recovery information"
                        },
                        "embeddings": {
                            "type": "array",
                            "items": {"type": "number"},
                            "title": "Embeddings",
                            "default": [],
                            "description": "Vector embeddings"
                        }
                    },
                    "description": "Note: message_id, memory_type, and subtype are auto-generated/auto-set"
                }
            }
        }
    }
}
# ==================== LONG TERM - PROCEDURAL ====================

PROCEDURAL_POST_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "ProceduralMemory",
                    "type": "object",
                    "required": ["agent_id", "memory", "subtype", "name"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "memory": {
                            "type": "object",
                            "title": "Memory",
                            "default": {}
                        },
                        "run_id": {
                            "type": "string",
                            "title": "Run Id",
                            "default": ""
                        },
                        "subtype": {
                            "type": "string",
                            "title": "Subtype",
                            "enum": ["agent_store", "tool_store", "workflow_store"],
                            "description": "Procedural subtype (required)"
                        },
                        "name": {
                            "type": "string",
                            "title": "Name",
                            "default": "",
                            "description": "Name of the procedure/config (required)"
                        },
                        "config": {
                            "type": "object",
                            "title": "Config",
                            "default": {},
                            "description": "Configuration data"
                        },
                        "integration": {
                            "type": "object",
                            "title": "Integration",
                            "default": {},
                            "description": "Integration details"
                        },
                        "status": {
                            "type": "string",
                            "title": "Status",
                            "enum": ["active", "deprecated"],
                            "default": "active"
                        },
                        "change_note": {
                            "type": "string",
                            "title": "Change Note",
                            "default": "",
                            "description": "Change notes"
                        },
                        "steps": {
                            "type": "array",
                            "items": {"type": "object"},
                            "title": "Steps",
                            "default": [],
                            "description": "Procedure steps"
                        }
                    },
                    "description": "Note: message_id and memory_type are auto-generated"
                }
            }
        }
    }
}

PROCEDURAL_PATCH_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "ProceduralMemoryUpdate",
                    "type": "object",
                    "required": ["agent_id", "message_id"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "message_id": {
                            "type": "string",
                            "title": "Message Id",
                            "default": ""
                        },
                        "memory_updates": {
                            "type": "object",
                            "title": "Memory Updates",
                            "default": {}
                        },
                        "remove_keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Remove Keys",
                            "default": []
                        },
                        "subtype": {
                            "type": "string",
                            "title": "Subtype",
                            "enum": ["agent_store", "tool_store", "workflow_store"],
                            "default": ""
                        },
                        "name": {
                            "type": "string",
                            "title": "Name",
                            "default": ""
                        },
                        "config_updates": {
                            "type": "object",
                            "title": "Config Updates",
                            "default": {}
                        },
                        "integration_updates": {
                            "type": "object",
                            "title": "Integration Updates",
                            "default": {}
                        },
                        "status": {
                            "type": "string",
                            "title": "Status",
                            "enum": ["active", "deprecated"],
                            "default": ""
                        },
                        "change_note": {
                            "type": "string",
                            "title": "Change Note",
                            "default": ""
                        },
                        "steps": {
                            "type": "array",
                            "items": {"type": "object"},
                            "title": "Steps",
                            "default": []
                        }
                    },
                    "description": "Note: memory_type is automatically set to 'procedural'"
                }
            }
        }
    }
}

# ==================== LONG TERM - WORKING PERSISTED ====================

WORKING_PERSISTED_POST_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "WorkingMemoryPersisted",
                    "type": "object",
                    "required": ["agent_id", "memory", "message_id"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "memory": {
                            "type": "object",
                            "title": "Memory",
                            "default": {}
                        },
                        "message_id": {
                            "type": "string",
                            "title": "Message Id",
                            "default": "",
                            "description": "Message ID from short-term memory"
                        },
                        "run_id": {
                            "type": "string",
                            "title": "Run Id",
                            "default": ""
                        },
                        "workflow_id": {
                            "type": "string",
                            "title": "Workflow Id",
                            "default": ""
                        },
                        "stages": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Stages",
                            "default": []
                        },
                        "current_stage": {
                            "type": "string",
                            "title": "Current Stage",
                            "default": ""
                        },
                        "context_log_summary": {
                            "type": "string",
                            "title": "Context Log Summary",
                            "default": ""
                        },
                        "user_query": {
                            "type": "string",
                            "title": "User Query",
                            "default": ""
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Tags",
                            "default": []
                        }
                    },
                    "description": "Note: Typically use POST /short-term/working/persist to automatically persist from Redis"
                }
            }
        }
    }
}
# Add after SEMANTIC_POST_SCHEMA

SUPERMEMORY_POST_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "SupermemorySemanticMemory",
                    "type": "object",
                    "required": ["agent_id", "content"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "content": {
                            "type": "string",
                            "title": "Content",
                            "default": "",
                            "description": "Text content to store in Supermemory"
                        },
                        "memory": {
                            "type": "object",
                            "title": "Memory",
                            "default": {},
                            "description": "Additional structured data"
                        },
                        "run_id": {
                            "type": "string",
                            "title": "Run Id",
                            "default": ""
                        },
                        "spaces": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Spaces",
                            "default": [],
                            "description": "Space IDs to add memory to"
                        },
                        "metadata_extra": {
                            "type": "object",
                            "title": "Metadata Extra",
                            "default": {},
                            "description": "Additional metadata"
                        }
                    },
                    "description": "Note: message_id is auto-generated"
                }
            }
        }
    }
}

WORKING_PERSISTED_PATCH_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "title": "WorkingMemoryPersistedUpdate",
                    "type": "object",
                    "required": ["agent_id", "message_id"],
                    "properties": {
                        "agent_id": {
                            "type": "string",
                            "title": "Agent Id",
                            "default": ""
                        },
                        "message_id": {
                            "type": "string",
                            "title": "Message Id",
                            "default": ""
                        },
                        "memory_updates": {
                            "type": "object",
                            "title": "Memory Updates",
                            "default": {}
                        },
                        "remove_keys": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Remove Keys",
                            "default": []
                        },
                        "workflow_id": {
                            "type": "string",
                            "title": "Workflow Id",
                            "default": ""
                        },
                        "stages": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Stages",
                            "default": []
                        },
                        "current_stage": {
                            "type": "string",
                            "title": "Current Stage",
                            "default": ""
                        },
                        "context_log_summary": {
                            "type": "string",
                            "title": "Context Log Summary",
                            "default": ""
                        },
                        "user_query": {
                            "type": "string",
                            "title": "User Query",
                            "default": ""
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "title": "Tags",
                            "default": []
                        }
                    }
                }
            }
        }
    }
}