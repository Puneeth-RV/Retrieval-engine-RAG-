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


async def generate_answer(
    question: str,
    chunks: list[str],
    filenames: list[str],
) -> str:
    """
    Generate an answer using Groq's Llama 3 model.

    Takes the user's question and the retrieved context chunks,
    builds a prompt, and returns the LLM's answer.
    """
    # Build context string with source labels
    context = "\n\n---\n\n".join(
        f"[Source: {filename}]\n{chunk}"
        for chunk, filename in zip(chunks, filenames)
    )

    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
        max_tokens=settings.MAX_TOKENS,
        temperature=0.2,
    )

    return response.choices[0].message.content
