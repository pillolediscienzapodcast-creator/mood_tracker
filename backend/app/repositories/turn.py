"""Accesso dati per i turni emotivi."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mood import EmotionalTurn


class TurnRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **fields) -> EmotionalTurn:
        turn = EmotionalTurn(**fields)
        self.db.add(turn)
        self.db.flush()
        return turn

    def get(self, turn_id: int) -> EmotionalTurn | None:
        return self.db.get(EmotionalTurn, turn_id)

    def get_latest(self, user_id: int) -> EmotionalTurn | None:
        stmt = (
            select(EmotionalTurn)
            .where(EmotionalTurn.user_id == user_id)
            .order_by(EmotionalTurn.id.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def list_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[EmotionalTurn]:
        stmt = (
            select(EmotionalTurn)
            .where(EmotionalTurn.user_id == user_id)
            .order_by(EmotionalTurn.id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
