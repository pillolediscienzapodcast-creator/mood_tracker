#!/bin/sh
set -e

# ---------------------------------------------------------------------------
# Auto-migrazione Alembic (PREDISPOSTA, non ancora attiva).
#
# La struttura è pronta: quando Alembic sarà verificato end-to-end contro
# il database, decommentare la riga seguente per applicare automaticamente
# le migration a ogni avvio del backend.
#
# uv run alembic upgrade head
# ---------------------------------------------------------------------------

exec "$@"
