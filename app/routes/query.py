from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.embeddings import embed_query
from app.services.generator import generate_answer
from app.services.vectorstore import search

router = APIRouter()


class QueryRequest(BaseModel):
    session_id: str
    question: str


@router.post("/api/query")
async def query_documents(request: QueryRequest):
    """
    Answer a question using the user's uploaded documents.

    Flow: embed question → search Qdrant (filtered by session) →
          send chunks to Groq → return answer with sources
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Step 1: Embed the question via Jina (~100ms)
    query_vector = await embed_query(request.question)

    # Step 2: Search Qdrant for matching chunks, filtered by session (~50ms)
    results = search(query_vector, request.session_id, settings.TOP_K)

    if not results:
        return {
            "answer": "I don't have any documents to search. Please upload some files first.",
            "sources": [],
        }

    # Step 3: Extract chunks and filenames from results
    chunks = [point.payload["text"] for point in results]
    filenames = [point.payload["filename"] for point in results]
    scores = [point.score for point in results]

    # Step 4: Generate answer via Groq Llama 3 (~500ms)
    answer = await generate_answer(request.question, chunks, filenames)

    # Step 5: Build source references
    sources = [
        {
            "filename": filename,
            "text_preview": chunk[:200] + "..." if len(chunk) > 200 else chunk,
            "score": round(score, 3),
        }
        for filename, chunk, score in zip(filenames, chunks, scores)
    ]

    return {"answer": answer, "sources": sources}
