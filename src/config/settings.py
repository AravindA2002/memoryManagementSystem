import os

# When your app runs inside the same docker-compose network, use service names
REDIS_URL   = os.getenv("REDIS_URL",   "redis://redis:6379/0")  # redis service
MONGO_URL   = os.getenv("MONGO_URL",   "mongodb://mongo:27017") # mongo service
MONGO_DB    = os.getenv("MONGO_DB",    "memory")

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost:")                # chroma service
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
