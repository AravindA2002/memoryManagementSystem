from __future__ import annotations
import os
import chromadb
from chromadb.config import Settings

class ChromaSemantic:
    def __init__(self, host: str | None = None, port: int | None = None):
        host = host or os.getenv("CHROMA_HOST", "localhost")
        port = int(port or os.getenv("CHROMA_PORT", "8000"))

        self.collection = None
       
        try:
           
            self.client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(allow_reset=False, anonymized_telemetry=False),
            )
            
            _ = self.client.heartbeat()
        except Exception as e:
            
            persist_dir = os.path.abspath("./.chroma")
            self.client = chromadb.PersistentClient(path=persist_dir, settings=Settings(allow_reset=False))
        
        self.collection = self.client.get_or_create_collection(
            "semantic_memories",
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, ids, documents, metadatas, embeddings=None):
        self.collection.add(
            ids=ids, documents=documents, metadatas=metadatas,
            embeddings=embeddings if embeddings is not None else None
        )

    def query_by_embedding(self, query_emb, top_k: int = 5):
        return self.collection.query(
        query_embeddings=[query_emb],
        n_results=top_k,
        include=["documents", "metadatas", "distances", "embeddings"],  
    )

