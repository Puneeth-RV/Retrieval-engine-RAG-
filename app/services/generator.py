from groq import AsyncGroq

from app.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.

Rules:
- Only use information from the provided context to answer
- If the context doesn't contain enough information, say so clearly
- Keep answers concise

Formatting (you MUST follow this exactly):
- Start directly with a 1-2 sentence answer — no label like "Summary:" or "Answer:"
- Use `## Heading` for section titles when needed (no bold for headings)
- Use `- item` for bullet lists (always use dash, never asterisk)
- Use `1. item` for numbered/sequential lists
- Use **bold** only for key terms and source filenames within sentences
- Separate sections with a blank line
- Never prefix your response with labels like "Summary:", "Answer:", "Response:", etc.
- Never use colons as fake headings like "Topic: description" — use proper headings instead"""


REWRITE_PROMPT = """Given the conversation history and a follow-up question, rewrite the follow-up into a standalone question that can be understood without the history. If the follow-up is already standalone, return it unchanged. Only output the rewritten question — no preamble, no explanation."""


async def rewrite_query(question: str, history: list[tuple[str, str]]) -> str:
    """
    Rewrite a follow-up question into a standalone one using chat history.
    Used to improve retrieval quality on follow-ups like "why?" or "tell me more".
    """
    if not history:
        return question

    history_text = "\n".join(
        f"User: {q}\nAssistant: {a}" for q, a in history
    )

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": REWRITE_PROMPT},
            {
                "role": "user",
                "content": f"Chat history:\n{history_text}\n\nFollow-up: {question}\n\nStandalone question:",
            },
        ],
        max_tokens=200,
        temperature=0.0,
    )

    rewritten = response.choices[0].message.content.strip()
    return rewritten or question


def _build_messages(
    question: str,
    chunks: list[str],
    filenames: list[str],
    history: list[tuple[str, str]] | None,
) -> list[dict]:
    context = "\n\n---\n\n".join(
        f"[Source: {filename}]\n{chunk}"
        for chunk, filename in zip(chunks, filenames)
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for prev_q, prev_a in history or []:
        messages.append({"role": "user", "content": prev_q})
        messages.append({"role": "assistant", "content": prev_a})
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {question}",
    })
    return messages


async def generate_answer(
    question: str,
    chunks: list[str],
    filenames: list[str],
    history: list[tuple[str, str]] | None = None,
) -> str:
    messages = _build_messages(question, chunks, filenames, history)

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        max_tokens=settings.MAX_TOKENS,
        temperature=0.2,
    )

    return response.choices[0].message.content
