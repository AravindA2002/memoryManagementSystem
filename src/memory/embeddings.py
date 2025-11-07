from typing import List
from openai import OpenAI
from ..config.settings import OPENAI_API_KEY, OPENAI_EMBED_MODEL


_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else OpenAI()


def openai_embed(text: str) -> List[float]:
    text = (text or "").strip()
    if not text:
        return []
    resp = _client.embeddings.create(model=OPENAI_EMBED_MODEL, input=text)
    return resp.data[0].embedding
