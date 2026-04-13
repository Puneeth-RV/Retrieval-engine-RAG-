from uuid import uuid4

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/session")
async def create_session():
    """
    Generate a new session ID for a visitor.

    The frontend calls this once on page load and stores the ID.
    All subsequent uploads and queries include this ID so each
    user's documents stay isolated.
    """
    return {"session_id": str(uuid4())}
