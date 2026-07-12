"""Nucleo adattivo: un passo online della dinamica emotiva.

Equazione di stato (Eulero-Maruyama):
    z_{t+1} = z_t + dt * [ -K (z_t - z0) + B u_t ]
Predizione generativa (predictive coding):
    u_pred = C * sigmoid(alpha * z_{t+1});  errore = u - u_pred
C e' stimata con Recursive Least Squares; B con discesa a gradiente a tasso
decrescente + leakage differenziato; K, z0, alpha si auto-regolano.

Il motore muta `ModelParams` in loco e restituisce un `StepResult`: sta al
chiamante (il servizio) risalvare i parametri aggiornati.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.engine import emotions
from app.engine.emotions import N_STATE
from app.engine.params import ModelParams

_RECENT_MAXLEN = 40


@dataclass
class StepResult:
    intensities: np.ndarray
    pad: np.ndarray
    dominant: list[tuple[str, float]]
    confidence: float
    pred_error_norm: float


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))


def _confidence(error: np.ndarray, P: np.ndarray) -> float:
    """Confidenza combinata (0-1): errore di predizione istantaneo +
    incertezza residua sui parametri (traccia della covarianza RLS)."""
    conf_errore = 1.0 / (1.0 + float(np.linalg.norm(error)))
    conf_parametri = 1.0 / (1.0 + float(np.trace(P)) / N_STATE)
    return float(np.clip(0.5 * conf_errore + 0.5 * conf_parametri, 0.0, 1.0))


def _traccia_statistiche(p: ModelParams, u: np.ndarray) -> None:
    """Aggiorna media/varianza di Welford delle feature grezze. Alimenta
    SOLO la baseline di digitazione (feature dedicata typing_speed_relative),
    non l'intero vettore: trasformare tutto l'input ad ogni turno creava un
    bersaglio di predizione in movimento per la RLS e destabilizzava."""
    p.feat_n += 1
    delta = u - p.feat_mean
    p.feat_mean = p.feat_mean + delta / p.feat_n
    delta2 = u - p.feat_mean
    p.feat_M2 = p.feat_M2 + delta * delta2


def step(
    p: ModelParams, u: np.ndarray, update: bool = True, learn_rate_scale: float = 1.0
) -> StepResult:
    """Un passo della dinamica.

    update=False -> sola inferenza (non tocca i parametri): utile per i
        sanity check o query che non devono influenzare l'apprendimento.
    learn_rate_scale -> scala SOLO l'apprendimento dei parametri, non il
        tracciamento dello stato. In uso live va ridotto (<1): testo reale
        fuori distribuzione puo' generare correzioni sproporzionate e drift.
        La personalizzazione live e' delegata soprattutto al feedback umano.
    """
    z, alpha = p.z, p.alpha

    if update:
        _traccia_statistiche(p, u)
        p.t += 1

    drift = -p.K @ (z - p.z0) + p.B @ u
    z_pred = z + p.dt * drift
    e_pred = _sigmoid(alpha * z_pred)
    u_pred = p.C @ e_pred
    error = u - u_pred

    if update:
        # --- RLS per C ---
        Px = p.P @ e_pred
        denom = p.rls_lambda + float(e_pred @ Px) + 1e-8
        k_gain = Px / denom
        p.C = p.C + learn_rate_scale * np.outer(error, k_gain)
        p.P = (p.P - np.outer(k_gain, Px)) / p.rls_lambda
        p.P = 0.5 * (p.P + p.P.T)

        # --- Gradiente + leak differenziato per B ---
        eta_B_t = learn_rate_scale * p.eta_B0 / (1.0 + p.t / p.tau_B)
        u_norm_sq = float(np.dot(u, u)) + 1e-4
        grad_B = np.outer(p.C.T @ error, u) / u_norm_sq
        fuori_dal_prior = 1.0 - p.B_intenzionale
        leak_effettivo = p.leak_B * (1.0 + 8.0 * fuori_dal_prior)
        p.B = p.B + eta_B_t * grad_B - leak_effettivo * eta_B_t * (p.B - p.B_prior)

        # --- Auto-regolazione di K ---
        volatility = np.abs(z_pred - z)
        p.K = p.K + learn_rate_scale * p.eta_K * (np.diag(volatility) - p.K) * 0.1
        p.K = np.clip(p.K, 0.01, 1.0) * np.eye(N_STATE)

        # --- Leak di z0 verso la MEDIA degli assi (nessun asse "scappa") ---
        z0_media = float(np.mean(p.z0))
        p.z0 = p.z0 + learn_rate_scale * (
            0.01 * (z_pred - p.z0) - p.leak_z0 * (p.z0 - z0_media)
        )

    p.z = z_pred

    if update:
        p.recent_e.append([float(x) for x in emotions.intensities(p.z, alpha)])
        if len(p.recent_e) > _RECENT_MAXLEN:
            p.recent_e = p.recent_e[-_RECENT_MAXLEN:]
        if len(p.recent_e) >= 10:
            var_obs = float(np.mean(np.var(np.array(p.recent_e), axis=0)))
            p.alpha = float(
                np.clip(alpha + p.eta_alpha * (p.target_variance - var_obs), 0.2, 5.0)
            )

    return StepResult(
        intensities=emotions.intensities(p.z, p.alpha),
        pad=emotions.pad(p.z, p.alpha),
        dominant=emotions.dominant_emotions(p.z, p.alpha, k=2),
        confidence=_confidence(error, p.P),
        pred_error_norm=float(np.linalg.norm(error)),
    )


def reset_state(p: ModelParams) -> None:
    """Riporta lo stato corrente al baseline personale appreso (z0),
    mantenendo i parametri di dinamica gia' calibrati."""
    p.z = p.z0.copy()


def diagnostics(p: ModelParams) -> dict:
    e0 = _sigmoid(p.alpha * p.z0)
    return {
        "model_version": p.model_version,
        "turni_processati": p.t,
        "feedback_ricevuti": p.feedback_count,
        "norma_B": float(np.linalg.norm(p.B)),
        "norma_C": float(np.linalg.norm(p.C)),
        "traccia_P": float(np.trace(p.P)),
        "alpha": float(p.alpha),
        "baseline_intensita": [round(float(x), 3) for x in e0],
        "baseline_saturato": bool(np.any(e0 > 0.95) or np.any(e0 < 0.05)),
    }
