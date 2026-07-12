# Import dei modelli per registrarli su Base.metadata (usato da Alembic).
from app.models.mood import (  # noqa: F401
    EmotionalFeedback,
    EmotionalModelState,
    EmotionalTurn,
)
from app.models.user import User  # noqa: F401
