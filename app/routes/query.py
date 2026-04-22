from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.services.embeddings import embed_query
from app.services.generator import generate_answer, rewrite_query
from app.services.history import append_turn, get_history
from app.services.vectorstore import search

router = APIRouter()


class QueryRequest(BaseModel):
    session_id: str
    question: str


@router.post("/api/query")
async def query_documents(request: QueryRequest):
    """
    Answer a question using the user's uploaded documents and chat history.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    history = get_history(request.session_id)
    search_question = await rewrite_query(request.question, history)
    query_vector = await embed_query(search_question)
    results = search(query_vector, request.session_id, settings.TOP_K)

    if not results:
        return {
            "answer": "I don't have any documents to search. Please upload some files first.",
            "sources": [],
        }

    chunks = [point.payload["text"] for point in results]
    filenames = [point.payload["filename"] for point in results]
    scores = [point.score for point in results]

    answer = await generate_answer(request.question, chunks, filenames, history)
    append_turn(request.session_id, request.question, answer)

    sources = [
        {
            "filename": filename,
            "text_preview": chunk[:200] + "..." if len(chunk) > 200 else chunk,
            "score": round(score, 3),
        }
        for filename, chunk, score in zip(filenames, chunks, scores)
    ]

    return {"answer": answer, "sources": sources}
