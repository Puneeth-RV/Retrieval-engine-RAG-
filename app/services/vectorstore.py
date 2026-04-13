from uuid import uuid4

from qdrant_client import QdrantClient, models

from app.config import settings

# Single client instance — reused across all requests
# (unlike the old code which created a new client per query)
client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)


def ensure_collection():
    """
    Create the Qdrant collection if it doesn't already exist.

    Called once on app startup.
    """
    collections = client.get_collections().collections
    if not any(c.name == settings.COLLECTION_NAME for c in collections):
        client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=settings.EMBEDDING_DIM,
                distance=models.Distance.COSINE,
            ),
        )


def upsert_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
):
    """
    Store embedded chunks in Qdrant with metadata.

    Each chunk gets a unique ID, its vector, and metadata
    (session_id, filename, chunk_index).
    """
    points = [
        models.PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={"text": chunk, **metadata},
        )
        for chunk, embedding, metadata in zip(chunks, embeddings, metadatas)
    ]
    client.upsert(collection_name=settings.COLLECTION_NAME, points=points)


def search(query_vector: list[float], session_id: str, top_k: int) -> list:
    """
    Search Qdrant for chunks matching the query, filtered by session_id.

    This is how we isolate each user's documents — only their chunks
    are searched, not everyone else's.
    """
    return client.query_points(
        collection_name=settings.COLLECTION_NAME,
        query=query_vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="session_id",
                    match=models.MatchValue(value=session_id),
                )
            ]
        ),
        limit=top_k,
    ).points
