from __future__ import annotations
from typing import Dict, List, Literal, Optional, Tuple
import numpy as np

from .models import Memory, MemoryTypeStrict
from .embeddings_openai import OpenAIEmbedder
from .db_redis import RedisStore
from .db_mongo import MongoLongTerm
from .db_chroma import ChromaSemantic
from .utils import cosine_sim, to_np

class MemoryRouter:
    

    def __init__(self, embedder: Optional[OpenAIEmbedder] = None):
        self.embedder = embedder or OpenAIEmbedder()
        self.redis = RedisStore()
        self.mongo = MongoLongTerm()
        self.chroma = ChromaSemantic()

    
    def store_memory(
        self,
        text: str,
        memory_type: MemoryTypeStrict,
        metadata: Optional[Dict[str, str]] = None,
        ttl_seconds: int = 3600,
        working_scope: Optional[str] = None,
    ) -> str:
        emb = self.embedder.encode([text])[0].tolist()
        mem = Memory(text=text, memory_type=memory_type, metadata=metadata or {}, embedding=emb)

        if memory_type == "short_term":
            self.redis.store(mem, ttl_seconds=ttl_seconds)
        elif memory_type == "working":
            scope = working_scope or (metadata or {}).get("scope") or "default"
            self.redis.store(mem, ttl_seconds=ttl_seconds, working_scope=scope)
        elif memory_type == "long_term":
            self.mongo.store(mem)
        elif memory_type == "semantic":
            safe_meta = {k: str(v) for k, v in (mem.metadata or {}).items()}
            safe_meta.update({
                "memory_type": mem.memory_type,
                "created_at": str(mem.created_at)
})
            self.chroma.add(
                ids=[mem.id],
                documents=[mem.text],
                metadatas=[safe_meta],
                embeddings=[mem.embedding],
)

        else:
            raise ValueError("Unsupported memory_type")

        return mem.id

   
    def retrieve(
        self,
        query: str,
        where: Literal["short_term", "working", "long_term", "semantic", "auto"] = "auto",
        top_k: int = 5,
        working_scope: Optional[str] = None,
    ) -> List[Tuple[Memory, float]]:
        q_emb = self.embedder.encode([query])[0]

        results: List[Tuple[Memory, float]] = []

        if where in ("short_term", "working", "auto"):
            subset_ids = None
            if where == "working" and working_scope:
                subset_ids = self.redis.scope_ids(working_scope)
            red_rows = self.redis.fetch_all(subset_ids=subset_ids)
            for m in red_rows:
                if m.embedding:
                    score = cosine_sim(q_emb, to_np(m.embedding))
                    results.append((m, score))

        if where in ("long_term", "auto"):
            long_rows = self.mongo.fetch_all(limit=10000)
            for m in long_rows:
                if m.embedding:
                    score = cosine_sim(q_emb, to_np(m.embedding))
                    results.append((m, score))

        if where in ("semantic", "auto"):
            res = self.chroma.query_by_embedding(q_emb.tolist(), top_k=top_k)
            ids = res.get("ids", [[]])[0]
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            dists = res.get("distances", [[]])[0]
            raw_embs = res.get("embeddings", [[]])
            embs = (raw_embs[0] if raw_embs and len(raw_embs) > 0 else [None] * len(ids))

            for _id, doc, meta, dist, emb in zip(ids, docs, metas, dists, embs):
                m = Memory(
                    id=_id,
                    text=doc,
                    memory_type="semantic",
                    metadata=meta,
                    embedding=emb,
                    created_at=meta.get("created_at", 0),
                    )
                score = 1 - float(dist) 
                results.append((m, score))


      
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
