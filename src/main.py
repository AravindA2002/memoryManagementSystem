

from __future__ import annotations
from router.memory_router import MemoryRouter
from router.embeddings_openai import OpenAIEmbedder
from dotenv import load_dotenv
load_dotenv()


def main():
    r = MemoryRouter(OpenAIEmbedder())

    print("Storing memories...")
    r.store_memory("Reminder: review the PR by 5pm", "short_term", {"user_id": "u1"}, ttl_seconds=3600)
    r.store_memory("Working goal: draft PRD for the memory agent", "working", {"scope": "sess42"}, ttl_seconds=7200)
    r.store_memory("Graduated MS in IT from ASU in 2025", "long_term", {"user_id": "u1"})
    r.store_memory("Invoice approval: extract -> validate -> route -> approve", "semantic", {"domain": "ops"})

    print("\nQueries:")
    for q, where in [
        ("what degree did the user finish", "long_term"),
        ("invoice approval steps", "semantic"),
        ("review the pull request", "auto"),
    ]:
        hits = r.retrieve(q, where=where, top_k=3, working_scope="sess42")
        print(f"\nQ: {q}  (where={where})")
        for m, score in hits:
            print(f"  score={score:.3f} | type={m.memory_type} | text={m.text}")

if __name__ == "__main__":
    main()
