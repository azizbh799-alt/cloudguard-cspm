# CloudGuard CSPM Backend

FastAPI + PostgreSQL backend for CloudGuard. AWS credentials are intentionally not stored; AWS discovery is simulated in this phase and the integration is reserved for the next phase.

## Run locally

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`. Start PostgreSQL with `docker compose up -d postgres`. The app creates tables on startup for development; Alembic is reserved for migration history.
