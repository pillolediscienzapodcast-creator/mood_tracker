# Immagine pinnata per digest (mai "latest"). Python 3.14 slim.
FROM python:3.14-slim@sha256:b877e50bd90de10af8d82c57a022fc2e0dc731c5320d762a27986facfc3355c1

# Binario uv pinnato per versione + digest.
COPY --from=ghcr.io/astral-sh/uv:0.11.28@sha256:0f36cb9361a3346885ca3677e3767016687b5a170c1a6b88465ec14aefec90aa /uv /uvx /bin/

# Utente di sistema non privilegiato.
RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/home/app/.cache/uv \
    PYTHONUNBUFFERED=1

# Layer di cache delle dipendenze: si invalida solo se cambiano i lock.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Codice applicativo + migrazioni.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY docker-entrypoint.sh ./

# Permessi al non-root e entrypoint eseguibile.
RUN chmod +x docker-entrypoint.sh \
    && chown -R app:app /app /home/app

USER app

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
