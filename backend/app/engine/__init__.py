"""Motore NOEMA — stima non-neurale dello stato emotivo.

Sistema dinamico adattivo (RLS + discesa a gradiente con leakage,
predictive coding) su uno stato a 8 emozioni di base (Plutchik). Modulo
PURO: non importa FastAPI ne' SQLAlchemy. Opera su `ModelParams`, che il
livello servizio carica dal database e risalva.

Prototipo di ricerca, non uno strumento diagnostico: le stime sono
inferenze da proxy comportamentali, non letture certe dello stato reale.
"""

from app.engine.emotions import EMOTIONS, N_STATE
from app.engine.features import FEATURE_ORDER, N_FEATURES
from app.engine.params import MODEL_VERSION, ModelParams, init_params

__all__ = [
    "EMOTIONS",
    "N_STATE",
    "FEATURE_ORDER",
    "N_FEATURES",
    "MODEL_VERSION",
    "ModelParams",
    "init_params",
]
