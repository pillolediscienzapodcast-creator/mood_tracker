"""Contenitore dei parametri del modello NOEMA (serializzabile).

A differenza del prototipo, il motore e' STATELESS PER-CHIAMATA: non e' un
oggetto che possiede lo stato fra un turno e l'altro. Tutto lo stato
mutabile (matrici apprese, stato emotivo corrente, statistiche personali,
contatori) vive in `ModelParams`, che il servizio carica dal database,
passa al motore e risalva. `to_dict()`/`from_dict()` producono/leggono una
struttura JSON-friendly, adatta a una colonna JSONB.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.engine.emotions import N_STATE
from app.engine.features import FEATURE_ORDER, N_FEATURES
from app.engine.lexicon import EMOTIONS

MODEL_VERSION = "0.4.0"

# Cluster di attivazione paralinguistica: feature che alimentano debolmente
# le emozioni ad alta attivazione (rabbia/paura/sorpresa) nel prior.
_CLUSTER_ATTIVAZIONE = [
    ("exclaim_rate", 0.15),
    ("repeated_char_rate", 0.10),
    ("error_rate", 0.15),
    ("typing_speed_relative", 0.10),
    ("rhythm_variability", 0.08),
]
_EMO_ATTIVAZIONE = ("rabbia", "paura", "sorpresa")


@dataclass
class ModelParams:
    """Tutti i parametri e lo stato del modello per una singola persona."""

    # Dinamica dello stato.
    K: np.ndarray  # (N_STATE, N_STATE) richiamo verso il baseline
    z0: np.ndarray  # (N_STATE,) baseline personale
    B: np.ndarray  # (N_STATE, N_FEATURES) mappa feature -> emozioni
    B_prior: np.ndarray  # (N_STATE, N_FEATURES) prior verso cui B rilassa
    B_intenzionale: np.ndarray  # (N_STATE, N_FEATURES) maschera connessioni deliberate
    C: np.ndarray  # (N_FEATURES, N_STATE) mappa generativa (RLS)
    P: np.ndarray  # (N_STATE, N_STATE) covarianza RLS

    # Stato emotivo corrente.
    z: np.ndarray  # (N_STATE,) stato grezzo
    alpha: float  # guadagno della sigmoide

    # Normalizzazione personale online (Welford) sulle feature grezze.
    feat_mean: np.ndarray
    feat_M2: np.ndarray
    feat_n: int

    # Storico recente delle intensita' (per l'auto-regolazione di alpha).
    recent_e: list = field(default_factory=list)

    # Iperparametri.
    dt: float = 0.9
    rls_lambda: float = 0.995
    eta_B0: float = 0.02
    tau_B: float = 220.0
    leak_B: float = 0.10
    leak_z0: float = 0.7
    eta_K: float = 0.02
    eta_alpha: float = 0.03
    target_variance: float = 0.05
    consolidation_every: int = 5

    # Contatori.
    t: int = 0
    feedback_count: int = 0
    model_version: str = MODEL_VERSION

    # ---- serializzazione ----
    def to_dict(self) -> dict:
        return {
            "model_version": self.model_version,
            "K": self.K.tolist(),
            "z0": self.z0.tolist(),
            "B": self.B.tolist(),
            "B_prior": self.B_prior.tolist(),
            "B_intenzionale": self.B_intenzionale.tolist(),
            "C": self.C.tolist(),
            "P": self.P.tolist(),
            "z": self.z.tolist(),
            "alpha": self.alpha,
            "feat_mean": self.feat_mean.tolist(),
            "feat_M2": self.feat_M2.tolist(),
            "feat_n": self.feat_n,
            "recent_e": [list(x) for x in self.recent_e],
            "dt": self.dt,
            "rls_lambda": self.rls_lambda,
            "eta_B0": self.eta_B0,
            "tau_B": self.tau_B,
            "leak_B": self.leak_B,
            "leak_z0": self.leak_z0,
            "eta_K": self.eta_K,
            "eta_alpha": self.eta_alpha,
            "target_variance": self.target_variance,
            "consolidation_every": self.consolidation_every,
            "t": self.t,
            "feedback_count": self.feedback_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModelParams":
        return cls(
            K=np.array(d["K"]),
            z0=np.array(d["z0"]),
            B=np.array(d["B"]),
            B_prior=np.array(d.get("B_prior", d["B"])),
            B_intenzionale=np.array(d["B_intenzionale"])
            if "B_intenzionale" in d
            else _maschera_intenzionale(),
            C=np.array(d["C"]),
            P=np.array(d["P"]),
            z=np.array(d["z"]),
            alpha=float(d["alpha"]),
            feat_mean=np.array(d["feat_mean"]),
            feat_M2=np.array(d["feat_M2"]),
            feat_n=int(d["feat_n"]),
            recent_e=[list(x) for x in d.get("recent_e", [])],
            dt=d.get("dt", 0.9),
            rls_lambda=d.get("rls_lambda", 0.995),
            eta_B0=d.get("eta_B0", 0.02),
            tau_B=d.get("tau_B", 220.0),
            leak_B=d.get("leak_B", 0.10),
            leak_z0=d.get("leak_z0", 0.7),
            eta_K=d.get("eta_K", 0.02),
            eta_alpha=d.get("eta_alpha", 0.03),
            target_variance=d.get("target_variance", 0.05),
            consolidation_every=d.get("consolidation_every", 5),
            t=int(d.get("t", 0)),
            feedback_count=int(d.get("feedback_count", 0)),
            model_version=d.get("model_version", MODEL_VERSION),
        )

    def personal_typing_baseline(self) -> dict:
        """Baseline di velocita' di digitazione appresa, RICONVERTITA in
        unita' grezze (tasti/secondo): le statistiche di Welford sono
        tracciate nello spazio gia' centrato/scalato, quindi vanno riportate
        indietro prima di confrontarle con una velocita' grezza. Confrontare
        unita' diverse produrrebbe sempre un valore estremo (bug di deriva
        del prototipo). Restituisce {} finche' i campioni sono pochi."""
        from app.engine.features import FEATURE_CENTER, FEATURE_SCALE

        if self.feat_n < 10:
            return {}
        idx = FEATURE_ORDER.index("typing_speed")
        std_scalato = float(np.sqrt(self.feat_M2[idx] / max(self.feat_n - 1, 1)))
        media_scalata = float(self.feat_mean[idx])
        scala = FEATURE_SCALE["typing_speed"]
        centro = FEATURE_CENTER.get("typing_speed", 0.0)
        return {
            "typing_speed_mean": media_scalata * scala + centro,
            "typing_speed_std": max(std_scalato * scala, 1e-6),
        }


def _init_B(rng: np.random.Generator) -> np.ndarray:
    """Prior psicologicamente motivato: ogni feature lessicale punta al
    proprio asse emotivo; il cluster paralinguistico alimenta debolmente
    rabbia/paura/sorpresa; la latenza alimenta la tristezza. Il modello
    non resta vincolato al prior: lo aggiorna in base ai propri errori."""
    B = rng.normal(0, 0.02, size=(N_STATE, N_FEATURES))
    for i, feat in enumerate(FEATURE_ORDER):
        if feat.startswith("lex_"):
            B[EMOTIONS.index(feat[4:]), i] += 0.5
    for feat, peso in _CLUSTER_ATTIVAZIONE:
        i = FEATURE_ORDER.index(feat)
        for emo in _EMO_ATTIVAZIONE:
            B[EMOTIONS.index(emo), i] += peso / 3.0
    B[EMOTIONS.index("tristezza"), FEATURE_ORDER.index("response_latency")] += 0.10
    return B


def _maschera_intenzionale() -> np.ndarray:
    """Maschera che marca ESPLICITAMENTE le celle di B corrispondenti a
    connessioni deliberate del prior. Necessaria perche' dedurle da una
    soglia sul valore casuale non e' affidabile (il rumore la supera per
    caso). Le celle marcate mantengono il leak normale; le altre ricevono
    un leak molto piu' forte verso zero."""
    mask = np.zeros((N_STATE, N_FEATURES))
    for i, feat in enumerate(FEATURE_ORDER):
        if feat.startswith("lex_"):
            mask[EMOTIONS.index(feat[4:]), i] = 1.0
    for feat, _ in _CLUSTER_ATTIVAZIONE:
        i = FEATURE_ORDER.index(feat)
        for emo in _EMO_ATTIVAZIONE:
            mask[EMOTIONS.index(emo), i] = 1.0
    mask[EMOTIONS.index("tristezza"), FEATURE_ORDER.index("response_latency")] = 1.0
    return mask


def init_params(
    seed: int = 0, K_scale: float = 0.35, P0_scale: float = 12.0, alpha: float = 1.0
) -> ModelParams:
    """Crea un modello "vergine" con il solo prior psicologico."""
    rng = np.random.default_rng(seed)
    B = _init_B(rng)
    return ModelParams(
        K=np.eye(N_STATE) * K_scale,
        z0=np.zeros(N_STATE),
        B=B,
        B_prior=B.copy(),
        B_intenzionale=_maschera_intenzionale(),
        C=rng.normal(0, 0.05, size=(N_FEATURES, N_STATE)),
        P=np.eye(N_STATE) * P0_scale,
        z=np.zeros(N_STATE),
        alpha=alpha,
        feat_mean=np.zeros(N_FEATURES),
        feat_M2=np.zeros(N_FEATURES),
        feat_n=0,
    )
