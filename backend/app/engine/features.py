"""Estrazione delle 24 feature da testo, dinamica di digitazione e metadati.

FEATURE_ORDER definisce l'ordine canonico degli assi del vettore di input `u`:
    8 lessicali (una per emozione) + 7 stilistiche + 5 di digitazione + 4 di
    interazione = 24.
Il vettore finale e' centrato, scalato e clippato per robustezza.
"""

from __future__ import annotations

import re

import numpy as np

from app.engine.lexicon import (
    DIMINUTORI,
    EMOJI,
    EMOTIONS,
    FRASI,
    INTENSIFICATORI,
    NEGATORI,
    PRONOMI_ALTRI,
    PRONOMI_SE,
)
from app.engine.matching import collassa_ripetute, normalizza_leet, trova_nel_lessico

# Tokenizzazione robusta: include cifre e simboli di censura nel token
# (altrimenti "ca**o"/"c4zzo" verrebbero spezzate ai bordi non alfabetici
# in frammenti irriconoscibili, prima ancora di consultare il lessico).
_TOKEN_RE = re.compile(r"[a-zàèéìòù0-9*#•]+(?:'[a-zàèéìòù0-9*#•]+)?")
_REPEAT_RE = re.compile(r"(.)\1{2,}")


def _normalizza_contesto(parole: list[str]) -> list[str]:
    return [normalizza_leet(collassa_ripetute(w)) for w in parole]


def text_features(text: str) -> dict[str, float]:
    """Feature linguistiche: 8 punteggi lessicali (normalizzati per parole
    riconosciute) + 7 stilistiche. Gestisce frasi idiomatiche, negazione
    (finestra indietro), intensificatori/diminutori (finestra
    bidirezionale), suffissi superlativi, emoji e scrittura non standard."""
    text_lower = text.lower()
    tokens = _TOKEN_RE.findall(text_lower)
    n = len(tokens) or 1

    emo_scores = {e: 0.0 for e in EMOTIONS}
    n_matched = 0

    i = 0
    while i < len(tokens):
        # Frasi idiomatiche prima delle singole parole (dalla piu' lunga).
        frase_trovata = None
        frase_lunghezza = 0
        for lunghezza in (4, 3, 2):
            candidata = tuple(tokens[i : i + lunghezza])
            if len(candidata) == lunghezza and candidata in FRASI:
                frase_trovata = FRASI[candidata]
                frase_lunghezza = lunghezza
                break
        if frase_trovata is not None:
            for emo, peso in frase_trovata.items():
                emo_scores[emo] += peso
            n_matched += 1
            i += frase_lunghezza
            continue

        entry = trova_nel_lessico(tokens[i])
        if entry is None:
            i += 1
            continue

        # Negazione: solo all'indietro (in italiano precede la parola negata).
        contesto_prima = _normalizza_contesto(tokens[max(0, i - 3) : i])
        negato = any(w in NEGATORI for w in contesto_prima)

        # Intensificatori/diminutori: finestra bidirezionale.
        contesto_dopo = _normalizza_contesto(tokens[i + 1 : i + 3])
        finestra = contesto_prima + contesto_dopo
        moltiplicatore = 1.0
        if any(w in INTENSIFICATORI for w in finestra):
            moltiplicatore = 1.5
        elif any(w in DIMINUTORI for w in finestra):
            moltiplicatore = 0.5
        if tokens[i].endswith(("issimo", "issima", "issimi", "issime")):
            moltiplicatore *= 1.3

        segno = -0.6 if negato else 1.0
        for emo, peso in entry.items():
            emo_scores[emo] += peso * moltiplicatore * segno
        n_matched += 1
        i += 1

    for emoji_str, entry in EMOJI.items():
        count = text_lower.count(emoji_str)
        if count:
            n_matched += count
            for emo, peso in entry.items():
                emo_scores[emo] += peso * count

    if n_matched > 0:
        emo_scores = {k: v / n_matched for k, v in emo_scores.items()}

    self_count = sum(1 for t in tokens if t in PRONOMI_SE)
    other_count = sum(1 for t in tokens if t in PRONOMI_ALTRI)
    self_focus_ratio = self_count / (self_count + other_count + 1)
    repeated_chars = len(_REPEAT_RE.findall(text))

    out = {f"lex_{emo}": emo_scores[emo] for emo in EMOTIONS}
    out.update(
        {
            "sentence_len": float(n),
            "exclaim_rate": text.count("!") / n,
            "question_rate": text.count("?") / n,
            "ellipsis_rate": text.count("...") / n,
            "caps_word_rate": sum(1 for w in text.split() if w.isupper() and len(w) > 1)
            / n,
            "self_focus_ratio": self_focus_ratio,
            "repeated_char_rate": repeated_chars / n,
        }
    )
    return out


def keystroke_features(
    keydown_times: list[float],
    backspace_count: int = 0,
    personal_baseline: dict | None = None,
) -> dict[str, float]:
    """Dinamica di digitazione. Se `personal_baseline` (media/std storiche
    della persona) e' fornita, calcola anche `typing_speed_relative`:
    "veloce" ha senso solo relativamente al proprio ritmo abituale."""
    if len(keydown_times) < 2:
        return {
            "typing_speed": 0.0,
            "rhythm_variability": 0.0,
            "burstiness": 0.0,
            "error_rate": 0.0,
            "typing_speed_relative": 0.0,
        }

    intervals = np.diff(np.asarray(keydown_times, dtype=float))
    mu, sigma = float(np.mean(intervals)), float(np.std(intervals))
    speed = 1.0 / (mu + 1e-6)
    variability = sigma / (mu + 1e-6)
    burstiness = (sigma - mu) / (sigma + mu + 1e-6)
    error_rate = backspace_count / max(len(keydown_times), 1)

    speed_relative = 0.0
    if personal_baseline and personal_baseline.get("typing_speed_std", 0) > 1e-6:
        speed_relative = (
            speed - personal_baseline["typing_speed_mean"]
        ) / personal_baseline["typing_speed_std"]

    return {
        "typing_speed": speed,
        "rhythm_variability": variability,
        "burstiness": burstiness,
        "error_rate": error_rate,
        "typing_speed_relative": float(np.clip(speed_relative, -4, 4)),
    }


def interaction_features(
    response_latency_s: float, is_followup: bool, followup_depth: int, hour_of_day: int
) -> dict[str, float]:
    return {
        "response_latency": float(response_latency_s),
        "is_followup": float(is_followup),
        "followup_depth": float(followup_depth),
        "circadian_phase": float(np.sin(2 * np.pi * hour_of_day / 24)),
    }


FEATURE_ORDER: list[str] = [f"lex_{e}" for e in EMOTIONS] + [
    "sentence_len",
    "exclaim_rate",
    "question_rate",
    "ellipsis_rate",
    "caps_word_rate",
    "self_focus_ratio",
    "repeated_char_rate",
    "typing_speed",
    "rhythm_variability",
    "burstiness",
    "error_rate",
    "typing_speed_relative",
    "response_latency",
    "is_followup",
    "followup_depth",
    "circadian_phase",
]
N_FEATURES = len(FEATURE_ORDER)  # 24

# Scala per riportare ogni feature grezza su un ordine di grandezza confrontabile.
FEATURE_SCALE: dict[str, float] = {
    "sentence_len": 20.0,
    "exclaim_rate": 1.0,
    "question_rate": 1.0,
    "ellipsis_rate": 1.0,
    "caps_word_rate": 1.0,
    "self_focus_ratio": 1.0,
    "repeated_char_rate": 1.0,
    "typing_speed": 6.0,
    "rhythm_variability": 2.0,
    "burstiness": 1.0,
    "error_rate": 1.0,
    "typing_speed_relative": 2.0,
    "response_latency": 15.0,
    "is_followup": 1.0,
    "followup_depth": 5.0,
    "circadian_phase": 1.0,
    **{f"lex_{e}": 1.0 for e in EMOTIONS},
}

# Centro "neutro" per feature che non hanno uno zero=assenza-di-segnale
# naturale (es. una latenza di 0s non e' neutra: e' anomala). Senza
# centratura, una feature sempre positiva collegata a un solo asse lo
# spinge sistematicamente verso l'alto turno dopo turno. Le feature di
# enfasi (esclamazioni, maiuscole...) NON vanno centrate: per loro
# zero=assenza di enfasi e' gia' il neutro corretto.
FEATURE_CENTER: dict[str, float] = {
    "sentence_len": 12.0,
    "typing_speed": 4.0,
    "rhythm_variability": 0.35,
    "response_latency": 6.0,
    "is_followup": 0.5,
    "followup_depth": 1.0,
}


def build_feature_vector(
    text_f: dict, key_f: dict, inter_f: dict, clip_value: float = 4.0
) -> np.ndarray:
    """Vettore di feature centrato, scalato e clippato (difesa contro input
    anomali o malformati: NaN/inf vengono neutralizzati)."""
    d = {**text_f, **key_f, **inter_f}
    raw = np.array(
        [
            (d.get(k, 0.0) - FEATURE_CENTER.get(k, 0.0)) / FEATURE_SCALE.get(k, 1.0)
            for k in FEATURE_ORDER
        ],
        dtype=float,
    )
    if not np.all(np.isfinite(raw)):
        raw = np.nan_to_num(raw, nan=0.0, posinf=clip_value, neginf=-clip_value)
    return np.clip(raw, -clip_value, clip_value)
