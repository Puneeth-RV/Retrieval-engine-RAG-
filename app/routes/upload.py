from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.services.chunker import chunk_text
from app.services.embeddings import embed_texts
from app.services.generator import suggest_questions
from app.services.pdf_parser import extract_text_from_pdf
from app.services.vectorstore import upsert_chunks

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("/api/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    session_id: str = Form(...),
):
    """
    Upload documents, chunk them, embed them, and store in Qdrant.

    Flow: files → extract text → chunk → embed via Jina → store in Qdrant
    Everything happens in memory — no files are saved to disk.
    """
    # Validate file count
    if len(files) > settings.MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_FILES_PER_UPLOAD} files per upload",
        )

    all_chunks = []
    all_metadatas = []

    for file in files:
        # Validate file extension
        filename = file.filename or "unknown"
        extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{extension}' not supported. Use PDF or TXT.",
            )

        # Read file bytes (stays in memory, never touches disk)
        content = await file.read()

        # Validate file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File '{filename}' is {size_mb:.1f}MB. Maximum is {settings.MAX_FILE_SIZE_MB}MB.",
            )

        # Extract text based on file type
        if extension == ".pdf":
            text = extract_text_from_pdf(content)
        else:
            text = content.decode("utf-8")

        if not text.strip():
            continue

        # Chunk the text
        chunks = chunk_text(text)

        # Build metadata for each chunk
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "session_id": session_id,
                "filename": filename,
                "chunk_index": i,
            })

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No text content found in uploaded files.")

    # Embed all chunks in one batch API call to Jina
    embeddings = await embed_texts(all_chunks)

    # Store in Qdrant with session_id metadata
    upsert_chunks(all_chunks, embeddings, all_metadatas)

    suggestions = await suggest_questions(all_chunks)

    return {
        "status": "ok",
        "files_processed": len(files),
        "chunks_created": len(all_chunks),
        "suggestions": suggestions,
    }
