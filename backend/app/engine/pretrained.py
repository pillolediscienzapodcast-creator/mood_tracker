"""Caricamento dei parametri pre-allenati (seed per i nuovi profili).

Un modello mai allenato ha confidenza strutturalmente bassa e riconosce
meno: per questo i nuovi utenti partono, quando disponibile, dai parametri
pre-allenati generati offline da `scripts/pretrain.py`. Se l'asset non
esiste si ricade su un modello vergine (solo prior psicologico).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.engine.params import ModelParams, init_params

_ASSET_PATH = Path(__file__).with_name("pretrained") / "noema_params.json"


def load_pretrained() -> ModelParams:
    if _ASSET_PATH.exists():
        with _ASSET_PATH.open(encoding="utf-8") as f:
            return ModelParams.from_dict(json.load(f))
    return init_params(seed=1)
