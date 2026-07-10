# Startup Template

Template full-stack, pronto all'uso, come base per nuovi progetti.

- **Backend**: FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL (gestione con [uv](https://docs.astral.sh/uv/))
- **Frontend**: Vue 3 · TypeScript · Vite · Pinia · Vue Router
- **Infrastruttura**: Docker Compose · GitHub Actions (CI)

## Versioni ufficiali del template

| Componente | Versione |
| ---------- | -------- |
| Python     | 3.14     |
| Node.js    | 22 LTS   |
| PostgreSQL | 16       |
| Docker Compose | v2   |

## Prerequisiti

- [Docker](https://www.docker.com/) + Docker Compose v2 (percorso consigliato)
- Per lo sviluppo locale senza Docker: [uv](https://docs.astral.sh/uv/) e [Node.js 22](https://nodejs.org/)

## Avvio rapido (Docker)

Due comandi, nient'altro:

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Servizi disponibili:

| Servizio   | URL                              |
| ---------- | -------------------------------- |
| Frontend   | http://localhost:5173            |
| Backend    | http://localhost:8000            |
| API docs   | http://localhost:8000/docs       |
| Healthcheck| http://localhost:8000/api/v1/health |
| PostgreSQL | localhost:5432                   |

> La homepage mostra lo stato del backend (🟢 Online / 🔴 Offline) leggendo l'endpoint di health.

Per fermare lo stack:

```bash
docker compose down        # mantiene i dati del database
docker compose down -v     # elimina anche il volume dati (pgdata)
```

## Configurazione

`backend/.env` è la **sorgente unica** della configurazione e **non è versionato**
(contiene segreti). Va creato copiando il template:

```bash
cp backend/.env.example backend/.env
```

| Variabile           | Descrizione                       |
| ------------------- | --------------------------------- |
| `APP_NAME`          | Nome dell'applicazione            |
| `APP_VERSION`       | Versione dell'applicazione        |
| `DEBUG`             | Abilita il logging SQL / debug    |
| `DATABASE_HOST`     | Host del database PostgreSQL      |
| `DATABASE_PORT`     | Porta del database                |
| `DATABASE_NAME`     | Nome del database                 |
| `DATABASE_USER`     | Utente del database               |
| `DATABASE_PASSWORD` | Password del database             |

> In Docker, `DATABASE_HOST` viene automaticamente impostato a `db` (nome del servizio):
> non serve modificarlo nel `.env`. I default delle credenziali del database in
> `docker-compose.yml` coincidono con `.env.example`, così `docker compose up` funziona
> senza flag aggiuntivi. Se cambi le credenziali, aggiorna `backend/.env` e ricrea il
> volume del database (`docker compose down -v`).

## Migrazioni database (Alembic)

Lo schema del database viene gestito esclusivamente con Alembic (nessun `create_all`).
Per applicare le migrazioni con lo stack in esecuzione:

```bash
docker compose exec backend uv run alembic upgrade head
```

Comandi utili (dalla cartella `backend/`, in locale):

```bash
uv run alembic upgrade head                        # applica le migrazioni
uv run alembic revision --autogenerate -m "descr"  # genera una nuova migrazione
uv run alembic downgrade -1                          # torna indietro di un passo
```

## Sviluppo locale (senza Docker)

Serve un PostgreSQL raggiungibile secondo i valori in `backend/.env`.

**Backend**

```bash
cd backend
uv sync                                  # installa le dipendenze (Python 3.14)
uv run alembic upgrade head              # crea lo schema
uv run uvicorn app.main:app --reload     # http://localhost:8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev                              # http://localhost:5173
```

## Test e qualità (backend)

```bash
cd backend
uv run ruff check .          # lint
uv run ruff format --check . # formattazione
uv run pytest                # test
```

## Integrazione continua

La pipeline GitHub Actions (`.github/workflows/ci.yml`) esegue ad ogni push/PR:

- **backend**: install · lint (ruff) · test (pytest)
- **frontend**: install · build
- **docker**: build delle immagini backend e frontend (nessun push)

## Struttura del progetto

```
startup-template/
├── backend/            # API FastAPI (uv, SQLAlchemy, Alembic)
│   ├── app/            # applicazione (api, core, db, models, schemas, services)
│   ├── alembic/        # migrazioni database
│   └── tests/          # test
├── frontend/           # SPA Vue 3 + TypeScript (Vite)
│   └── src/            # router, stores, services, views, components
├── docker-compose.yml  # orchestrazione db + backend + frontend
└── .github/workflows/  # CI
```

## Licenza

[MIT](LICENSE) © 2026 Massimo Dell'Erba
