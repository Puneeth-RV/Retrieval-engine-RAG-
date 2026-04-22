from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes import session, upload, query
from app.services.vectorstore import ensure_collection

static_dir = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on app startup - ensures Qdrant collection exists."""
    ensure_collection()
    yield


app = FastAPI(title="DocuQuery", lifespan=lifespan)

# Allow frontend to call the API (needed for local dev and deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(session.router)
app.include_router(upload.router)
app.include_router(query.router)

# Serve static assets (CSS, JS)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Serve index.html at root
@app.get("/")
async def root():
    return FileResponse(static_dir / "index.html")
