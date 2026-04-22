---
title: DocuQuery
emoji: 📄
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# DocuQuery

**Upload documents. Ask questions. Get grounded answers.**

A production-style RAG (Retrieval-Augmented Generation) web app. Drop in your PDFs or text files, ask anything in natural language, and get concise answers backed by citations from your own documents — with conversational follow-ups that remember context.

> **Live demo:** https://puneeth-rv-docuquery.hf.space

---

## Features

- **Ask anything** — natural-language Q&A over your own documents
- **Sources with every answer** — see the exact chunks the LLM used, with match scores
- **Conversational memory** — follow-ups like *"why?"* or *"tell me more"* work; queries are rewritten into standalone questions for better retrieval
- **Smart starters** — after upload, the app suggests three specific questions tailored to your document
- **Session isolation** — each visitor gets their own private workspace (no one sees your files)
- **Dark / light theme** — warm, minimal UI with Apple-style squircle corners where supported
- **Mobile-friendly** — full responsive layout down to 360px

---

## How It Works

```
┌──────────┐   ┌──────────┐   ┌──────────────┐   ┌──────────────┐
│  Upload  │ → │  Chunk   │ → │ Embed (Jina) │ → │ Store        │
│ PDF/TXT  │   │  text    │   │  768-dim     │   │ (Qdrant)     │
└──────────┘   └──────────┘   └──────────────┘   └──────────────┘

┌──────────┐   ┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────┐
│ Question │ → │ Rewrite w/ │ → │  Embed       │ → │ Search       │ → │ Generate │
│          │   │ chat hist. │   │  (Jina)      │   │ (Qdrant)     │   │ (Groq)   │
└──────────┘   └────────────┘   └──────────────┘   └──────────────┘   └──────────┘
```

Retrieved chunks are injected as context; Groq's Llama 3.1 generates the answer and the frontend renders it with source cards.

---

## Tech Stack

| Layer            | Technology                                       |
| ---------------- | ------------------------------------------------ |
| Backend          | FastAPI (async Python)                           |
| Embeddings       | [Jina](https://jina.ai/) `jina-embeddings-v2-base-en` (768-dim) |
| Vector DB        | [Qdrant Cloud](https://qdrant.tech/) with payload-filter user isolation |
| LLM              | [Groq](https://groq.com/) `llama-3.1-8b-instant` |
| Frontend         | Vanilla HTML / CSS / JS (no framework)           |
| Hosting          | [Hugging Face Spaces](https://huggingface.co/spaces) (Docker) |

**No** local model weights, **no** `torch`, **no** `llama_index` — the entire backend is well under 100 MB of Python, so it fits easily on free-tier infra.

---

## Design Decisions

- **APIs over local models.** Jina + Groq + Qdrant Cloud keeps the server tiny and startup instant. No GPU, no 2 GB Docker image.
- **One collection, many users.** User isolation is done via a Qdrant payload index on `session_id` — simpler than per-user collections and cheaper than per-user databases.
- **Query rewriting before retrieval.** Vague follow-ups (*"and the second one?"*) get rewritten into standalone questions using chat history — dramatically better recall than feeding raw follow-ups to the embedder.
- **Files never hit disk.** PDF/TXT parsing happens in-memory; the ephemeral server holds no state.
- **Session ID in request body, not cookies.** No cookie consent, no server-side session store — history lives in a simple in-process dict, capped at 6 turns.

---

## Run Locally

```bash
# 1. Clone
git clone https://github.com/Puneeth-RV/DocuQuery.git
cd DocuQuery

# 2. Environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure secrets (see .env.example)
cat > .env <<EOF
JINA_API_KEY=your_jina_key
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_key
GROQ_API_KEY=your_groq_key
EOF

# 4. Run
uvicorn app.main:app --reload
```

Open http://localhost:8000

All API keys have generous free tiers — no credit card needed to run this.

---

## Project Structure

```
app/
├── main.py                 FastAPI app, lifespan, static mount
├── config.py               Pydantic settings (reads .env / env vars)
├── routes/
│   ├── session.py          GET  /api/session   — issue a session UUID
│   ├── upload.py           POST /api/upload    — ingest documents
│   └── query.py            POST /api/query     — answer a question
├── services/
│   ├── chunker.py          Recursive char splitter (sentence-aware)
│   ├── pdf_parser.py       PyMuPDF text extraction (in-memory)
│   ├── embeddings.py       Async Jina client (batch + single)
│   ├── vectorstore.py      Qdrant client singleton + session filter
│   ├── generator.py        Groq answer, query rewriter, suggestions
│   └── history.py          Per-session chat memory (thread-safe)
└── static/
    ├── index.html
    ├── style.css           Theming, glass-like cards, squircle corners
    └── script.js           Upload, chat, markdown rendering
```

---

## API

| Method | Endpoint       | Body                                   | Response                                                    |
| ------ | -------------- | -------------------------------------- | ----------------------------------------------------------- |
| GET    | `/api/session` | —                                      | `{ session_id }`                                            |
| POST   | `/api/upload`  | multipart: `files[]` + `session_id`    | `{ files_processed, chunks_created, suggestions }`          |
| POST   | `/api/query`   | `{ session_id, question }`             | `{ answer, sources: [{ filename, text_preview, score }] }`  |

---

## Limits

Tuned conservatively for free-tier hosting:
- Max **5 files** per upload, **10 MB** each
- Max **2000 chars** per question
- Chat memory: last **6 turns** per session
- Retrieval: top **5** chunks per query

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, project conventions, and the pull-request checklist. For anything non-trivial, please open an issue first so we can align on the approach.

## License

[MIT](LICENSE) © Puneeth RV
