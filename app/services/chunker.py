from app.config import settings


def chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping chunks, breaking at sentence boundaries.

    This replaces llama_index's SentenceSplitter — same idea, zero dependencies.
    """
    chunk_size = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP

    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary instead of mid-word
        if end < len(text):
            for separator in [". ", "! ", "? ", "\n\n", "\n", " "]:
                last_break = text[start:end].rfind(separator)
                if last_break > chunk_size // 2:
                    end = start + last_break + len(separator)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks
