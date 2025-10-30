from __future__ import annotations
import os
from typing import List
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from .models import Memory

class MongoLongTerm:
    def __init__(self, uri: str | None = None, db: str | None = None, collection: str | None = None):
        uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db = db or os.getenv("MONGODB_DB", "memorydb")
        collection = collection or os.getenv("MONGODB_COLLECTION_LONGTERM", "long_term_memories")
        self.client = MongoClient(uri)
        self.col: Collection = self.client[db][collection]
        self.col.create_index([("created_at", ASCENDING)], background=True)

    def store(self, mem: Memory):
        self.col.insert_one(mem.model_dump())

    def fetch_all(self, limit: int = 10000) -> List[Memory]:
        docs = self.col.find({}, {"_id": 0}).sort("created_at", ASCENDING).limit(limit)
        return [Memory(**d) for d in docs]
