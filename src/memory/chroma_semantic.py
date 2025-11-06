# src/memory/chroma_semantic.py
from __future__ import annotations

import chromadb
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE

class ChromaSemanticStore:
    """
    Minimal, v2-compatible Chroma client for data operations.
    - Does NOT use admin calls (no get_tenant / get_admin_client).
    - Uses default tenant/database which exist on the server.
    """

    def __init__(self, host: str = "localhost", port: int = 8000):
        """
        host: can be "localhost" OR "http://localhost"
        port: server HTTP port (default 8000)
        """
        # For v2, either pass (host, port) OR a full base URL via 'host'.
        # Both of the following are valid:
        #   chromadb.HttpClient(host="localhost", port=8000, ...)
        #   chromadb.HttpClient(host="http://localhost:8000", ...)
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False,
            ),
            tenant=DEFAULT_TENANT,        # "default_tenant"
            database=DEFAULT_DATABASE,    # "default_database"
        )

    # convenience helpers you might be calling elsewhere
    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(name=name)

    def delete_collection(self, name: str):
        try:
            self.client.delete_collection(name)
        except Exception:
            # ignore if it doesn't exist
            pass

    def list_collections(self):
        return self.client.list_collections()
