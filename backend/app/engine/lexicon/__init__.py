"""Risorsa linguistica italiana per il motore NOEMA.

Il lessico emotivo e le risorse annesse (negatori, intensificatori, emoji,
frasi idiomatiche, coordinate PAD) sono trattati come ASSET DATI statici:
sono caricati una sola volta da `lessico_it.json` e resi disponibili come
strutture in memoria. Non contengono logica — l'algoritmo che li consuma
vive in `app.engine.features` e `app.engine.matching`.

ONESTA' METODOLOGICA: e' un lessico costruito a mano (~488 voci), non una
risorsa validata psicometricamente su larga scala. Copre le forme piu'
comuni, non l'intero vocabolario emotivo italiano.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_ASSET_PATH = Path(__file__).with_name("lessico_it.json")


@lru_cache(maxsize=1)
def _load() -> dict:
    with _ASSET_PATH.open(encoding="utf-8") as f:
        return json.load(f)


_data = _load()

# Le 8 emozioni di base (modello di Plutchik). L'ordine e' significativo:
# definisce l'ordine degli assi dello stato e delle feature lessicali.
EMOTIONS: list[str] = list(_data["emotions"])

# parola (minuscolo) -> {emozione: peso 0-1}
LESSICO: dict[str, dict[str, float]] = _data["lessico"]

# Insiemi di modificatori linguistici.
NEGATORI: frozenset[str] = frozenset(_data["negatori"])
INTENSIFICATORI: frozenset[str] = frozenset(_data["intensificatori"])
DIMINUTORI: frozenset[str] = frozenset(_data["diminutori"])

# Emoji/emoticon -> {emozione: peso}. Ricerca per substring nel testo.
EMOJI: dict[str, dict[str, float]] = _data["emoji"]

# Frasi idiomatiche: tuple di token -> {emozione: peso}. Riconosciute come
# unita' PRIMA della scomposizione a singola parola (es. "non vedo l'ora"
# e' anticipazione positiva, non una negazione).
FRASI: dict[tuple[str, ...], dict[str, float]] = {
    tuple(item["tokens"]): item["weights"] for item in _data["frasi"]
}

# Parole tipicamente censurate nella scrittura reale (ca**o, m***a...),
# usate per disambiguare il matching jolly.
PAROLE_CENSURABILI: frozenset[str] = frozenset(_data["parole_censurabili"])

# Pronomi per la feature di auto-focus (correlato psicolinguistico debole).
PRONOMI_SE: frozenset[str] = frozenset(_data["pronomi_se"])
PRONOMI_ALTRI: frozenset[str] = frozenset(_data["pronomi_altri"])

# Coordinate approssimative (Valenza, Arousal, Dominanza) per emozione.
# Valori illustrativi da affective computing (Russell, Plutchik), non
# costanti psicometriche precise.
PAD_COORDS: dict[str, tuple[float, float, float]] = {
    k: tuple(v) for k, v in _data["pad_coords"].items()
}

__all__ = [
    "EMOTIONS",
    "LESSICO",
    "NEGATORI",
    "INTENSIFICATORI",
    "DIMINUTORI",
    "EMOJI",
    "FRASI",
    "PAROLE_CENSURABILI",
    "PRONOMI_SE",
    "PRONOMI_ALTRI",
    "PAD_COORDS",
]
