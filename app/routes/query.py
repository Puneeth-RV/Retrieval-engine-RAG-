import json

from pydantic import BaseModel

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.services.embeddings import embed_query
from app.services.generator import generate_answer_stream, rewrite_query
from app.services.history import append_turn, get_history
from app.services.vectorstore import search

router = APIRouter()


class QueryRequest(BaseModel):
    session_id: str
    question: str


@router.post("/api/query")
async def query_documents(request: QueryRequest):
    """
    Stream an answer using the user's uploaded documents and chat history.

    Emits NDJSON events: {"type": "sources", ...}, {"type": "token", ...},
    {"type": "done"}, or {"type": "error", ...}.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    history = get_history(request.session_id)
    search_question = await rewrite_query(request.question, history)
    query_vector = await embed_query(search_question)
    results = search(query_vector, request.session_id, settings.TOP_K)

    def sse(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    async def event_stream():
        # Initial comment flushes headers past proxies that wait for first byte
        yield ": connected\n\n"

        if not results:
            yield sse({
                "type": "token",
                "text": "I don't have any documents to search. Please upload some files first.",
            })
            yield sse({"type": "sources", "sources": []})
            yield sse({"type": "done"})
            return

        chunks = [point.payload["text"] for point in results]
        filenames = [point.payload["filename"] for point in results]
        scores = [point.score for point in results]

        sources = [
            {
                "filename": filename,
                "text_preview": chunk[:200] + "..." if len(chunk) > 200 else chunk,
                "score": round(score, 3),
            }
            for filename, chunk, score in zip(filenames, chunks, scores)
        ]
        yield sse({"type": "sources", "sources": sources})

        full_answer = []
        try:
            async for delta in generate_answer_stream(
                request.question, chunks, filenames, history
            ):
                full_answer.append(delta)
                yield sse({"type": "token", "text": delta})
        except Exception as e:
            yield sse({"type": "error", "message": str(e)})
            return

        answer_text = "".join(full_answer)
        if answer_text.strip():
            append_turn(request.session_id, request.question, answer_text)

        yield sse({"type": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
