import os

# Valori di default per far avviare Settings() senza un file .env
# (es. in CI). Non sovrascrivono eventuali variabili già presenti.
os.environ.setdefault("APP_NAME", "Startup Template")
os.environ.setdefault("APP_VERSION", "0.1.0")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_PORT", "5432")
os.environ.setdefault("DATABASE_NAME", "startup_template")
os.environ.setdefault("DATABASE_USER", "postgres")
os.environ.setdefault("DATABASE_PASSWORD", "postgres")
