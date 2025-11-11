from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.short_term import router as short_term_router
from .routers.long_term import router as long_term_router
from .routers.retrieval import router as retrieval_router


app = FastAPI(title="Memory Storage API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(short_term_router, prefix="/v1/memory", tags=["short-term"])
app.include_router(long_term_router,  prefix="/v1/memory", tags=["long-term"])
#app.include_router(retrieval_router,  prefix="/v1/memory", tags=["retrieve"])

@app.get("/health")
async def health():
    return {"ok": True}
