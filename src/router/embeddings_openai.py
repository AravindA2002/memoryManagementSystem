from __future__ import annotations
import os, time
from typing import List
from openai import OpenAI
import numpy as np

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

class OpenAIEmbedder:
    
    def __init__(self, model: str | None = None):
        self.model = model or DEFAULT_MODEL
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def encode(self, texts: List[str], max_retries: int = 4, backoff: float = 0.8) -> np.ndarray:
        for attempt in range(max_retries):
            try:
                resp = self.client.embeddings.create(model=self.model, input=texts)
                vecs = [d.embedding for d in resp.data]
                arr = np.asarray(vecs, dtype=np.float32)
                
                norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
                return (arr / norms).astype(np.float32)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(backoff * (2 ** attempt))
        raise RuntimeError("Unreachable")
