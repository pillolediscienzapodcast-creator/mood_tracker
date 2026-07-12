"""Feedback supervisionato e consolidamento periodico.

Dopo ogni stima la persona monitorata puo' confermare o correggere. La
correzione sposta subito lo stato corrente verso il target (misura
bayesiana, non un reset). I feedback si accumulano e vengono consolidati
periodicamente rielaborando B e C con i target FORNITI DALL'UMANO invece
dell'auto-predizione.
"""

from __future__ import annotations

import numpy as np

from app.engine.emotions import N_STATE
from app.engine.lexicon import EMOTIONS
from app.engine.params import ModelParams


def target_da_emozione(
    alpha: float, emozione: str, intensita: float = 0.75
) -> np.ndarray:
    """Costruisce lo stato-target `z` che, sotto la sigmoide con guadagno
    `alpha`, produce l'intensita' desiderata sull'asse dell'emozione
    indicata (e neutro sugli altri)."""
    target = np.zeros(N_STATE)
    j = EMOTIONS.index(emozione)
    logit = np.log(intensita / (1 - intensita + 1e-6) + 1e-6)
    target[j] = logit / max(alpha, 1e-3)
    return target


def apply_feedback(
    p: ModelParams,
    corretto: bool,
    emozione_corretta: str | None = None,
    intensita: float = 0.75,
    gain: float = 0.4,
) -> np.ndarray:
    """Corregge lo stato corrente in base al feedback e incrementa il
    contatore. Ritorna il target `z` usato (da bufferizzare per il
    consolidamento). `corretto=True` conferma lo stato corrente; altrimenti
    lo sposta verso l'emozione indicata con guadagno `gain`."""
    if not corretto and emozione_corretta not in EMOTIONS:
        raise ValueError(f"emozione_corretta deve essere una di {EMOTIONS}")

    target = (
        p.z.copy()
        if corretto
        else target_da_emozione(p.alpha, emozione_corretta, intensita)
    )
    p.z = p.z + gain * (target - p.z)
    p.feedback_count += 1
    return target


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def consolidate(p: ModelParams, buffer: list[tuple[np.ndarray, np.ndarray]]) -> None:
    """Rielabora i feedback accumulati (coppie vettore-feature `u` +
    target `z`), aggiornando B e C con peso maggiore di un passo online
    ordinario. `buffer` proviene dai turni con feedback non ancora
    consolidato (persistiti nel database)."""
    if not buffer:
        return
    for u, target in buffer:
        e_target = _sigmoid(p.alpha * target)
        u_pred = p.C @ e_target
        error = u - u_pred

        Px = p.P @ e_target
        denom = p.rls_lambda + float(e_target @ Px) + 1e-8
        k_gain = Px / denom
        p.C = p.C + 1.5 * np.outer(error, k_gain)

        grad_B = np.outer(p.C.T @ error, u) / (float(np.dot(u, u)) + 1e-4)
        p.B = p.B + 0.08 * grad_B - p.leak_B * 0.08 * (p.B - p.B_prior)
