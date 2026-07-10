# Backend — Startup Template

API FastAPI con SQLAlchemy 2, Alembic e PostgreSQL. Dipendenze gestite con
[uv](https://docs.astral.sh/uv/). Python **3.14**.

## Setup

```bash
cp .env.example .env    # sorgente unica di configurazione (non versionata)
uv sync                 # crea il virtualenv e installa le dipendenze
```

## Avvio

```bash
uv run uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Documentazione (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

Richiede un PostgreSQL raggiungibile secondo i valori in `.env`.

## Migrazioni (Alembic)

Lo schema è gestito solo tramite migrazioni (nessun `create_all`).

```bash
uv run alembic upgrade head                        # applica le migrazioni
uv run alembic revision --autogenerate -m "descr"  # genera una migrazione dai modelli
uv run alembic downgrade -1                          # rollback di un passo
```

## Qualità

```bash
uv run ruff check .           # lint
uv run ruff format --check .  # formattazione
uv run pytest                 # test
```

## Struttura

```
app/
├── api/            # dependency (get_db) e router versionati (/api/v1)
│   └── v1/routes/  # endpoint (health, users)
├── core/           # configurazione (pydantic-settings)
├── db/             # engine, session, Base declarative
├── models/         # modelli SQLAlchemy
├── schemas/        # schemi Pydantic
└── services/       # accesso al database (repository)
alembic/            # migrazioni
tests/              # test (pytest)
```
