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
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["agent_id", "memory"],
                    "properties": {
                        "agent_id": {"type": "string"},
                        "memory": {"type": "object"},
                        "normalized_text": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "metadata": {"type": "object"}
                    }
                }
            }
        }
    }
}

SEMANTIC_PATCH_SCHEMA = {
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["agent_id", "message_id", "memory_type"],
                    "properties": {
                        "agent_id": {"type": "string"},
                        "message_id": {"type": "string"},
                        "memory_type": {"type": "string", "enum": ["semantic"], "default": "semantic"},
                        "memory_updates": {"type": "object"},
                        "remove_keys": {"type": "array", "items": {"type": "string"}},
                        "normalized_text": {"type": "string"}
                    }
                }
            }
        }
    }
}

# ==================== LONG TERM - EPISODIC ====================

EPISODIC_POST_SCHEMA = {
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["agent_id", "memory", "subtype"],
                    "properties": {
                        "agent_id": {"type": "string"},
                        "memory": {"type": "object"},
                        "subtype": {
                            "type": "string",
                            "enum": ["conversational", "summaries", "observations", "working_persisted"]
                        },
                        "conversation_id": {"type": "string"},
                        "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                        "run_id": {"type": "string"},
                        "workflow_id": {"type": "string"}
                    }
                }
            }
        }
    }
}

# ==================== LONG TERM - PROCEDURAL ====================

PROCEDURAL_POST_SCHEMA = {
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["agent_id", "memory", "subtype", "name"],
                    "properties": {
                        "agent_id": {"type": "string"},
                        "memory": {"type": "object"},
                        "subtype": {
                            "type": "string",
                            "enum": ["agent_store", "tool_store", "workflow_store"]
                        },
                        "name": {"type": "string"},
                        "config": {"type": "object"},
                        "steps": {"type": "array", "items": {"type": "object"}},
                        "status": {"type": "string", "enum": ["active", "deprecated"], "default": "active"}
                    }
                }
            }
        }
    }
}

PROCEDURAL_PATCH_SCHEMA = {
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["agent_id", "message_id", "memory_type"],
                    "properties": {
                        "agent_id": {"type": "string"},
                        "message_id": {"type": "string"},
                        "memory_type": {"type": "string", "enum": ["procedural"], "default": "procedural"},
                        "memory_updates": {"type": "object"},
                        "remove_keys": {"type": "array", "items": {"type": "string"}},
                        "config_updates": {"type": "object"},
                        "status": {"type": "string", "enum": ["active", "deprecated"]}
                    }
                }
            }
        }
    }
}