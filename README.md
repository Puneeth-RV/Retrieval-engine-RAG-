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

Upload documents. Ask questions. Get answers.

A RAG (Retrieval-Augmented Generation) web app that lets users upload their own PDFs and text files, then ask natural language questions and receive AI-generated answers grounded in the uploaded content — with source citations.

## How It Works

```
Upload:  Files → Chunk text → Embed via Jina API → Store in Qdrant Cloud
Query:   Question → Embed → Search Qdrant → Generate answer via Groq (Llama 3)
```

Each user gets an isolated session — your documents are only visible to you.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Embeddings | Jina Embeddings API |
| Vector Database | Qdrant Cloud |
| LLM | Groq (Llama 3.1 8B) |
| Frontend | HTML / CSS / JavaScript |
| Hosting | Hugging Face Spaces |

## Run Locally

1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/your-repo.git
   cd your-repo
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys (see `.env.example`):
   ```
   JINA_API_KEY=your_key
   QDRANT_URL=your_qdrant_cloud_url
   QDRANT_API_KEY=your_key
   GROQ_API_KEY=your_key
   ```

4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Open http://localhost:8000 in your browser.

## Project Structure

```
app/
  main.py              # FastAPI app entry point
  config.py            # Environment-based configuration
  routes/
    session.py         # GET  /api/session — create user session
    upload.py          # POST /api/upload  — upload and process documents
    query.py           # POST /api/query   — ask questions, get answers
  services/
    chunker.py         # Text splitting with sentence-boundary awareness
    pdf_parser.py      # PDF text extraction (PyMuPDF)
    embeddings.py      # Jina API client for text embeddings
    vectorstore.py     # Qdrant Cloud client for vector storage and search
    generator.py       # Groq LLM client for answer generation
  static/
    index.html         # Frontend UI
    style.css          # Styling
    script.js          # Frontend logic
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/session` | Returns a new session ID |
| POST | `/api/upload` | Upload files (multipart form: files + session_id) |
| POST | `/api/query` | Ask a question (JSON: session_id + question) |
