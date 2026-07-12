"""Accesso dati per i feedback umani."""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.mood import EmotionalFeedback


class FeedbackRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, turn_id: int, user_id: int, corretto: bool, emozione_corretta: str | None
    ) -> EmotionalFeedback:
        fb = EmotionalFeedback(
            turn_id=turn_id,
            user_id=user_id,
            corretto=corretto,
            emozione_corretta=emozione_corretta,
        )
        self.db.add(fb)
        self.db.flush()
        return fb

    def list_unconsolidated(self, user_id: int) -> list[EmotionalFeedback]:
        stmt = (
            select(EmotionalFeedback)
            .where(
                EmotionalFeedback.user_id == user_id,
                EmotionalFeedback.consolidated.is_(False),
            )
            .order_by(EmotionalFeedback.id)
        )
        return list(self.db.scalars(stmt).all())

    def mark_consolidated(self, ids: list[int]) -> None:
        if not ids:
            return
        self.db.execute(
            update(EmotionalFeedback)
            .where(EmotionalFeedback.id.in_(ids))
            .values(consolidated=True)
        )
