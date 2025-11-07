# src/memory/chroma_semantic.py

import re
import uuid
import chromadb
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
from ..config.settings import CHROMA_BASE_URL, CHROMA_HOST, CHROMA_PORT

_VALID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,61}[A-Za-z0-9]$")  # 3-63, safe chars

def _sanitize_collection_name(raw: str) -> str:
    s = str(raw).strip()
    # replace illegal chars
    s = re.sub(r"[^A-Za-z0-9_-]", "-", s)
    # ensure length >= 3
    if len(s) < 3:
        s = f"agent-{s}".ljust(3, "0")
    # ensure starts/ends alnum
    if not s[0].isalnum():
        s = f"a{s}"
    if not s[-1].isalnum():
        s = f"{s}0"
    # truncate to 63 while keeping alnum end
    s = s[:63]
    if not s[-1].isalnum():
        s = s[:-1] + "0"
    # final guard
    if not _VALID.fullmatch(s):
        # fallback to deterministic safe name
        s = ("agent-" + re.sub(r"[^A-Za-z0-9]", "", s))[:63]
        if len(s) < 3:
            s = "agent-000"

    return s

def _norm_text(primary: str, fallback: str) -> str:
    t = (primary or "").strip()
    if not t or t.lower() == "string":  # protect against Swagger defaults
        t = (fallback or "").strip()
    return t

class ChromaSemanticStore:
    def __init__(self, host: str | None = None, port: int | None = None):
        self._base = CHROMA_BASE_URL.strip()
        self._host = (host or CHROMA_HOST).strip()
        self._port = port or CHROMA_PORT
        self._client = None

    def _client_or_connect(self):
        if self._client:
            return self._client
        if self._base:
            self._client = chromadb.HttpClient(
                host=self._base,
                settings=Settings(allow_reset=True, anonymized_telemetry=False),
                tenant=DEFAULT_TENANT, database=DEFAULT_DATABASE,
            )
        else:
            self._client = chromadb.HttpClient(
                host=self._host, port=self._port,
                settings=Settings(allow_reset=True, anonymized_telemetry=False),
                tenant=DEFAULT_TENANT, database=DEFAULT_DATABASE,
            )
        return self._client

    def get_or_create_collection(self, name: str):
        safe = _sanitize_collection_name(name)
        return self._client_or_connect().get_or_create_collection(name=safe)

    def delete_collection(self, name: str):
        try:
            safe = _sanitize_collection_name(name)
            self._client_or_connect().delete_collection(safe)
        except Exception:
            pass

    def list_collections(self):
        return self._client_or_connect().list_collections()

    async def add(self, agent_id: str, text: str, normalized_text: str, embed_fn) -> str:
        col = self.get_or_create_collection(agent_id)
        norm = _norm_text(normalized_text, text)  # <- use memory if normalized is empty/"string"
        emb = embed_fn(norm)
        mem_id = str(uuid.uuid4())
        col.add(
        ids=[mem_id],
        documents=[text],
        embeddings=[emb],
        metadatas=[{"normalized_text": norm}],
    )
        return mem_id
    
    

    async def similarity_search(self, agent_id: str, query: str, embed_fn, k: int = 10):
        col = self.get_or_create_collection(agent_id)
        qvec = embed_fn(query)
        res = col.query(query_embeddings=[qvec], n_results=k)
        out = []
        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        for i, _id in enumerate(ids):
            out.append({
                "id": _id,
                "document": docs[i] if i < len(docs) else None,
                "distance": dists[i] if i < len(dists) else None,
                "metadata": metas[i] if i < len(metas) else {},
            })
        return out
