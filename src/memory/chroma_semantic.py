

import re
import uuid
from typing import Optional, List
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

    async def add(
        self, 
        agent_id: str, 
        text: str, 
        normalized_text: str, 
        embed_fn,
        message_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> str:
        col = self.get_or_create_collection(agent_id)
        norm = _norm_text(normalized_text, text)  # <- use memory if normalized is empty/"string"
        emb = embed_fn(norm)
        mem_id = str(uuid.uuid4())
        
        metadata = {"normalized_text": norm}
        if message_id:
            metadata["message_id"] = message_id
        if run_id:
            metadata["run_id"] = run_id
            
        col.add(
            ids=[mem_id],
            documents=[text],
            embeddings=[emb],
            metadatas=[metadata],
        )
        return mem_id

    async def update(
        self,
        agent_id: str,
        message_id: str,
        text: str,
        normalized_text: str,
        embed_fn
    ) -> bool:
        
        col = self.get_or_create_collection(agent_id)
        
        # Find the entry by message_id
        try:
            results = col.get(where={"message_id": message_id})
            
            if not results or not results.get("ids"):
                return False
            
            # Get the old ID
            old_id = results["ids"][0]
            
            # Delete the old entry
            col.delete(ids=[old_id])
            
            # Add new entry with updated content
            norm = _norm_text(normalized_text, text)
            emb = embed_fn(norm)
            new_id = str(uuid.uuid4())
            
            col.add(
                ids=[new_id],
                documents=[text],
                embeddings=[emb],
                metadatas={"normalized_text": norm, "message_id": message_id},
            )
            
            return True
            
        except Exception as e:
            print(f"Error updating semantic memory in ChromaDB: {e}")
            return False

    async def delete_by_message_id(self, agent_id: str, message_id: str) -> bool:
        
        try:
            col = self.get_or_create_collection(agent_id)
            results = col.get(where={"message_id": message_id})
            
            if not results or not results.get("ids"):
                return False
            
            col.delete(ids=results["ids"])
            return True
            
        except Exception as e:
            print(f"Error deleting semantic memory from ChromaDB: {e}")
            return False

    async def delete_all(self, agent_id: str) -> int:
       
        try:
            col = self.get_or_create_collection(agent_id)
            
            # Get all entries
            results = col.get()
            count = len(results.get("ids", []))
            
            if count > 0:
                # Delete collection and recreate empty
                self.delete_collection(agent_id)
                self.get_or_create_collection(agent_id)
            
            return count
            
        except Exception as e:
            print(f"Error deleting all semantic memories from ChromaDB: {e}")
            return 0

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