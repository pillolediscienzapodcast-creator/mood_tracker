from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

# Import dei modelli: popola Base.metadata con tutte le tabelle
# (necessario perché l'autogenerate le "veda").
import app.models  # noqa: F401
from alembic import context

# Sorgente unica della connection string: derivata da app/core/config.py.
# NON viene ricostruita qui, per evitare duplicazioni di DATABASE_URL.
from app.db.base import Base
from app.db.database import DATABASE_URL

# Oggetto di configurazione Alembic (legge alembic.ini).
config = context.config

# Inietta la connection string a runtime.
# Le eventuali `%` vanno raddoppiate per l'interpolazione di ConfigParser.
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

# Logging da alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata target per l'autogenerate delle migration.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Migrazioni in modalità 'offline' (genera SQL senza connettersi)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Migrazioni in modalità 'online' (connessione reale al database)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
