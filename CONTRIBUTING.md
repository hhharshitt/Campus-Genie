# Contributing to CampusGenie

## Development Setup

### Prerequisites
- Docker >= 24.0 and Docker Compose >= 2.0
- Python 3.11+ (for running backend locally without Docker)
- Node.js is not required

### Running locally (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

**Frontend:**
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

You will need ChromaDB and Ollama running separately, or update
`BACKEND_URL` in `.env` to point to the Dockerized services.

## Code Style

- Follow PEP 8 for Python code.
- Use type hints on all function signatures.
- Add docstrings to all public classes and methods.
- Keep functions small and focused. Prefer composition over inheritance.

## Commit Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/).

```
feat(scope):    new feature
fix(scope):     bug fix
refactor(scope): code change without behaviour change
chore(scope):   maintenance, tooling, config
docs(scope):    documentation only
test(scope):    test additions or corrections
```

## Project Structure Notes

- `backend/app/rag/` — the core RAG pipeline. Changes here affect answer quality directly.
- `backend/app/routes/` — FastAPI route handlers. Keep these thin; push logic into `rag/`.
- `frontend/app.py` — single-file Streamlit app. Sections are clearly delimited.

## Submitting Changes

1. Fork the repository
2. Create a branch: `git checkout -b feat/your-feature`
3. Make your changes with appropriate tests
4. Open a pull request with a clear description
