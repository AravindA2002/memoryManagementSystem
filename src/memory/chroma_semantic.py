
from __future__ import annotations

import chromadb
import uuid

from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
from ..config.settings import CHROMA_BASE_URL, CHROMA_HOST, CHROMA_PORT

class ChromaSemanticStore:
   

    def __init__(self, host: str | None = None, port: int | None = None):
      
        host = host if host is not None else CHROMA_HOST
        port = port if port is not None else CHROMA_PORT

        if CHROMA_BASE_URL:
          
            self.client = chromadb.HttpClient(
                host=CHROMA_BASE_URL,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False,
                ),
                tenant=DEFAULT_TENANT,
                database=DEFAULT_DATABASE,
            )
        else:
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(
                    allow_reset=True,
                    anonymized_telemetry=False,
                ),
                tenant=DEFAULT_TENANT,
                database=DEFAULT_DATABASE,
            )

  
    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(name=name)

    def delete_collection(self, name: str):
        try:
            self.client.delete_collection(name)
        except Exception:
            pass

    def list_collections(self):
        return self.client.list_collections()
    

    async def add(self, agent_id: str, text: str, normalized_text: str, embed_fn) -> str:
        """
        Store a single semantic memory into the agent collection.
        """
        col = self.get_or_create_collection(agent_id)
        emb = embed_fn(normalized_text)
        mem_id = str(uuid.uuid4())
        col.add(
            ids=[mem_id],
            documents=[text],
            embeddings=[emb],
            metadatas=[{"normalized_text": normalized_text}],
        )
        return mem_id

    async def similarity_search(self, agent_id: str, query: str, embed_fn, k: int = 10):
        """
        Return top-k semantic matches for the query in this agent's collection.
        """
        col = self.get_or_create_collection(agent_id)
        qvec = embed_fn(query)
        res = col.query(query_embeddings=[qvec], n_results=k)
        # Shape into a friendlier list
        out = []
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        dists = res.get("distances", [[]])[0] or res.get("embeddings", [[]])  # guard
        metas = res.get("metadatas", [[]])[0]
        for i, _id in enumerate(ids):
            out.append({
                "id": _id,
                "document": docs[i] if i < len(docs) else None,
                "distance": dists[i] if i < len(dists) else None,
                "metadata": metas[i] if i < len(metas) else {},
            })
        return out
