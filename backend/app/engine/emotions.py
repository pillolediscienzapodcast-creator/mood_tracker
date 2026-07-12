"""Spazio degli stati emotivi: 8 emozioni di base + PAD derivato.

Lo stato "grezzo" z evolve senza vincoli in R^N_STATE; l'intensita'
osservabile di ciascuna emozione e' sigmoid(alpha*z) in (0,1) — 0.5 =
assente/neutro, verso 1 = massima intensita'. Valenza/Arousal/Dominanza
(PAD) sono DERIVATE come combinazione pesata dello scostamento dal neutro
delle intensita' correnti: sono un riassunto a valle, non lo stato primario.
"""

from __future__ import annotations

import numpy as np

from app.engine.lexicon import EMOTIONS, PAD_COORDS

N_STATE = len(EMOTIONS)  # 8

# Matrice (N_STATE, 3) delle coordinate PAD, ordinata come EMOTIONS.
_PAD_MATRIX = np.array([PAD_COORDS[e] for e in EMOTIONS], dtype=float)


def intensities(z: np.ndarray, alpha: float) -> np.ndarray:
    """Intensita' (0,1) di ciascuna emozione: sigmoid(alpha*z), con clip
    per stabilita' numerica."""
    return 1.0 / (1.0 + np.exp(-np.clip(alpha * z, -30, 30)))


def pad(z: np.ndarray, alpha: float) -> np.ndarray:
    """(Valenza, Arousal, Dominanza) derivate dallo SCOSTAMENTO DAL NEUTRO
    (0.5) delle intensita'. Usare l'intensita' grezza sarebbe un bug: a
    riposo (tutte a 0.5) produrrebbe gia' un PAD sbilanciato invece che
    neutro."""
    scostamento = intensities(z, alpha) - 0.5
    return np.clip(scostamento @ _PAD_MATRIX, -1.0, 1.0)


def dominant_emotions(
    z: np.ndarray, alpha: float, k: int = 2, soglia: float = 0.515
) -> list[tuple[str, float]]:
    """Le k emozioni piu' intense sopra la soglia minima, come lista di
    (nome, intensita') ordinata per intensita' decrescente. La soglia va
    fissata SOPRA 0.5 (neutro sigmoide), altrimenti il rumore attorno al
    neutro verrebbe scambiato per emozione presente; ma vicina a 0.5,
    perche' un singolo turno produce per design una spinta modesta."""
    inten = intensities(z, alpha)
    ordine = np.argsort(-inten)
    risultato: list[tuple[str, float]] = []
    for i in ordine[:k]:
        if inten[i] >= soglia:
            risultato.append((EMOTIONS[i], float(inten[i])))
    return risultato
