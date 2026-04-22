import httpx

from app.config import settings

JINA_ENDPOINT = "https://api.jina.ai/v1/embeddings"


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a batch of texts using Jina's API.

    Used when uploading documents - sends all chunks in one API call.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            JINA_ENDPOINT,
            headers={"Authorization": f"Bearer {settings.JINA_API_KEY}"},
            json={
                "model": settings.JINA_MODEL,
                "input": texts,
            },
            timeout=30.0,
        )
        response.raise_for_status()

    data = response.json()["data"]
    # Sort by index to ensure order matches input
    data.sort(key=lambda x: x["index"])
    return [item["embedding"] for item in data]


async def embed_query(text: str) -> list[float]:
    """
    Embed a single query string.

    Convenience wrapper - used when a user asks a question.
    """
    embeddings = await embed_texts([text])
    return embeddings[0]
