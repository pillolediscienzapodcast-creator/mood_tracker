"""Accesso dati per lo stato del modello per-utente."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mood import EmotionalModelState


class ModelStateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> EmotionalModelState | None:
        stmt = select(EmotionalModelState).where(EmotionalModelState.user_id == user_id)
        return self.db.scalars(stmt).first()

    def get_for_update(self, user_id: int) -> EmotionalModelState | None:
        """Carica lo stato con lock di riga (SELECT ... FOR UPDATE) per
        serializzare i turni concorrenti dello stesso utente ed evitare
        aggiornamenti persi sullo stato incrementale."""
        stmt = (
            select(EmotionalModelState)
            .where(EmotionalModelState.user_id == user_id)
            .with_for_update()
        )
        return self.db.scalars(stmt).first()

    def create(
        self,
        user_id: int,
        params: dict,
        model_version: str,
        n_turns_trained: int = 0,
        feedback_count: int = 0,
    ) -> EmotionalModelState:
        state = EmotionalModelState(
            user_id=user_id,
            params=params,
            model_version=model_version,
            n_turns_trained=n_turns_trained,
            feedback_count=feedback_count,
        )
        self.db.add(state)
        self.db.flush()
        return state

    def update_params(
        self,
        state: EmotionalModelState,
        params: dict,
        n_turns_trained: int,
        feedback_count: int,
    ) -> EmotionalModelState:
        state.params = params
        state.n_turns_trained = n_turns_trained
        state.feedback_count = feedback_count
        state.row_version += 1
        self.db.flush()
        return state
