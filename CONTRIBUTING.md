# Contributing to DocuQuery

Thanks for wanting to contribute! This project is a small, focused RAG web app, so the guidelines below stay intentionally lightweight.

## Ways to contribute

- **Report a bug** - open an issue using the Bug Report template.
- **Propose a feature** - open an issue using the Feature Request template and describe the use case.
- **Submit a pull request** - fix a bug, improve docs, or build a feature that's already been discussed in an issue.

For anything non-trivial, please open an issue first so we can align on the approach before you invest time.

## Development setup

```bash
# 1. Fork and clone your fork
git clone https://github.com/YOUR_USERNAME/DocuQuery.git
cd DocuQuery

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the example env file and fill in your API keys
cp .env.example .env
# Edit .env with your JINA / QDRANT / GROQ keys

# 5. Run the dev server
uvicorn app.main:app --reload
```

Open http://localhost:8000 - changes to Python files hot-reload automatically. For frontend changes (HTML/CSS/JS), just refresh the browser.

## Project layout

See the "Project Structure" section in [README.md](README.md).

Summary of what goes where:

- `app/routes/` - thin FastAPI endpoints. Parse input, call services, return JSON.
- `app/services/` - business logic. No FastAPI imports here; these are plain async functions so they can be reused and tested.
- `app/static/` - frontend. Vanilla JS, no build step.

## Style

- **Python**: follow PEP 8 defaults. Prefer `async def` for anything that awaits I/O. Keep functions short.
- **JavaScript**: 4-space indent, double quotes for strings, camelCase. No frameworks, no build step.
- **CSS**: use the existing CSS variables for colors. Keep media queries in the mobile section at the bottom of the file.
- **ASCII only** in code files (docstrings, comments, prompts). The README can use unicode for diagrams and typography.

## Pull request checklist

- [ ] Branch off `master` with a descriptive name (`fix/upload-timeout`, `feat/export-chat`)
- [ ] Run the app locally and manually verify the feature or fix works
- [ ] Keep the PR focused - one logical change per PR
- [ ] Update `README.md` if you added a user-visible feature or changed the API
- [ ] Reference the issue the PR closes (`Closes #123`)

## Commit messages

Short, imperative, lowercase where natural. Examples:

```
Add streaming support for query responses
Fix Qdrant payload index on session_id
Tighten mobile layout on very narrow screens
```

## Questions?

Open an issue with the `question` label or start a discussion on the repo.
