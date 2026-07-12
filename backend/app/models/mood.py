from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmotionalModelState(Base):
    """Parametri appresi del modello NOEMA per una singola persona.

    Un record attivo per utente. `params` e' il blob JSONB serializzato da
    ModelParams (matrici B/C/P/K/z0, stato z, alpha, statistiche di Welford,
    iperparametri). `row_version` serve al lock ottimistico: i turni
    concorrenti dello stesso utente vanno serializzati per non corrompere
    lo stato incrementale.
    """

    __tablename__ = "emotional_model_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    model_version: Mapped[str] = mapped_column(String(20))
    params: Mapped[dict] = mapped_column(JSONB)
    n_turns_trained: Mapped[int] = mapped_column(Integer, default=0)
    feedback_count: Mapped[int] = mapped_column(Integer, default=0)
    row_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EmotionalTurn(Base):
    """Un turno ingerito + la stima prodotta.

    `feature_vector` viene salvato apposta: il consolidamento del feedback
    ha bisogno del vettore `u` del turno, non ricostruibile in un backend
    stateless. `text` e' nullable: la memorizzazione del testo in chiaro e'
    opzionale (vedi settings.store_turn_text).
    """

    __tablename__ = "emotional_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Input di interazione.
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_latency_s: Mapped[float] = mapped_column(Float)
    backspace_count: Mapped[int] = mapped_column(Integer)
    is_followup: Mapped[bool] = mapped_column(Boolean)
    followup_depth: Mapped[int] = mapped_column(Integer)
    hour_of_day: Mapped[int] = mapped_column(Integer)

    # Feature e stima.
    feature_vector: Mapped[list] = mapped_column(JSONB)
    emotions: Mapped[dict] = mapped_column(JSONB)
    dominant_emotions: Mapped[list] = mapped_column(JSONB)
    valence: Mapped[float] = mapped_column(Float)
    arousal: Mapped[float] = mapped_column(Float)
    dominance: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)
    label: Mapped[str] = mapped_column(Text)
    no_lexicon_match: Mapped[bool] = mapped_column(Boolean)

    feedback: Mapped[list["EmotionalFeedback"]] = relationship(
        back_populates="turn", cascade="all, delete-orphan"
    )


class EmotionalFeedback(Base):
    """Correzione umana su una stima.

    Il "buffer di consolidamento" del prototipo diventa una query: i
    feedback con `consolidated=False` vengono rielaborati in batch ogni
    `consolidation_every` (default 5).
    """

    __tablename__ = "emotional_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    turn_id: Mapped[int] = mapped_column(
        ForeignKey("emotional_turns.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    corretto: Mapped[bool] = mapped_column(Boolean)
    emozione_corretta: Mapped[str | None] = mapped_column(String(20), nullable=True)
    consolidated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    turn: Mapped["EmotionalTurn"] = relationship(back_populates="feedback")
