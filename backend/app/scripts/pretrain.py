"""Pre-training offline del modello NOEMA.

Genera un dataset sintetico di turni (frasi variate sulle 8 emozioni),
allena un modello vergine in modalita' batch (learn_rate pieno), esegue la
batteria di correttezza semantica prima/dopo e — solo se il punteggio resta
sopra la soglia di sicurezza — salva i parametri come asset
`app/engine/pretrained/noema_params.json`, usato come seed per i nuovi
profili. Meglio nessun asset (fallback a modello vergine) che uno che ha
imparato associazioni sbagliate.

Uso:
    uv run python -m app.scripts.pretrain [n_per_regime] [seed]
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np

from app.engine import model as engine_model
from app.engine.features import (
    build_feature_vector,
    interaction_features,
    keystroke_features,
    text_features,
)
from app.engine.params import init_params
from app.engine.sanity import run_sanity_checks

SOGLIA_SICUREZZA = 0.75
_ASSET_PATH = (
    Path(__file__).resolve().parents[1] / "engine" / "pretrained" / "noema_params.json"
)

# Template di frasi + profili di digitazione per regime emotivo. Il campo
# "regime" NON viene mai letto dal modello: l'apprendimento resta
# auto-supervisionato, guidato dall'errore di predizione.
TEMPLATES = {
    "gioia": {
        "testi": [
            "Sono felice e contento, che bella giornata",
            "Grazie mille, sono davvero entusiasta del risultato!",
            "Che fantastico regalo, sono felicissimo 😊",
            "Oggi mi sento davvero allegro e soddisfatto",
            "Non potrei essere piu' felice di cosi'",
        ],
        "backspace": (0, 2),
        "n_keys": (30, 60),
        "base_interval": 0.12,
        "latency": (2, 6),
    },
    "fiducia": {
        "testi": [
            "Sono sereno e rilassato, tutto va bene",
            "Mi fido di questo processo, andra' tutto bene",
            "Va tutto tranquillo, nessuna fretta",
            "Sono abbastanza sicuro che funzionera'",
            "Mi sento calmo e in controllo della situazione",
        ],
        "backspace": (0, 1),
        "n_keys": (25, 50),
        "base_interval": 0.20,
        "latency": (5, 12),
    },
    "paura": {
        "testi": [
            "Ho paura, sono molto ansioso e nervoso",
            "Sono preoccupato, non so se andra' tutto bene",
            "Mi sento in ansia, ho il panico per la scadenza",
            "Sono terrorizzato all'idea di sbagliare tutto 😱",
            "Non riesco a stare tranquillo, sono molto agitato",
        ],
        "backspace": (2, 6),
        "n_keys": (25, 50),
        "base_interval": 0.13,
        "latency": (2, 6),
    },
    "sorpresa": {
        "testi": [
            "Non me lo aspettavo, che sorpresa incredibile",
            "Wow, non ci posso credere, sono senza parole",
            "Che notizia inaspettata, sono davvero stupito",
            "Non avrei mai immaginato una cosa simile",
            "Incredibile, questo risultato mi ha scioccato",
        ],
        "backspace": (1, 4),
        "n_keys": (25, 55),
        "base_interval": 0.10,
        "latency": (1, 4),
    },
    "tristezza": {
        "testi": [
            "Sono triste e stanco, che brutta giornata",
            "Mi sento giu', non ho voglia di fare niente oggi",
            "Sono tristissimo, mi sento malissimo oggi 😢",
            "Non sono per niente felice di questa situazione",
            "E' stata una giornata pesante, sono esausto",
        ],
        "backspace": (1, 3),
        "n_keys": (18, 40),
        "base_interval": 0.28,
        "latency": (8, 20),
    },
    "disgusto": {
        "testi": [
            "Che schifo, questa cosa mi disgusta profondamente",
            "Trovo tutto questo davvero irritante e fastidioso",
            "E' una situazione insopportabile, mi da' il voltastomaco",
            "Non sopporto proprio questo modo di fare",
            "Che cosa ripugnante, non ci posso pensare",
        ],
        "backspace": (2, 5),
        "n_keys": (25, 50),
        "base_interval": 0.11,
        "latency": (2, 5),
    },
    "rabbia": {
        "testi": [
            "Sono arrabbiato e frustrato, odio questo problema",
            "Sono furioso, questo e' assolutamente inaccettabile!!!",
            "Basta, sono esasperato, voglio una spiegazione ORA",
            "Sono incazzato nero per come sono andate le cose",
            "Non sono affatto contento di questo trattamento 😡",
        ],
        "backspace": (4, 10),
        "n_keys": (35, 75),
        "base_interval": 0.08,
        "latency": (1, 3),
    },
    "anticipazione": {
        "testi": [
            "Non vedo l'ora, sono molto curioso di scoprire cosa succedera'",
            "Sto aspettando con ansia buone notizie",
            "Sono molto curioso di vedere come andra' a finire",
            "Ho grandi speranze per il prossimo progetto",
            "Sto pianificando il futuro con entusiasmo",
        ],
        "backspace": (0, 2),
        "n_keys": (30, 60),
        "base_interval": 0.14,
        "latency": (3, 8),
    },
}


def _make_record(regime: str, rng: np.random.Generator) -> dict:
    cfg = TEMPLATES[regime]
    text = str(rng.choice(cfg["testi"]))
    n_keys = int(rng.integers(*cfg["n_keys"]))
    # Rumore ampio, sovrapposto fra regimi: la velocita' di digitazione da
    # sola NON deve diventare un segnale affidabile (sarebbe una scorciatoia
    # che generalizza male). Il contenuto lessicale resta il segnale primario.
    base = cfg["base_interval"] * rng.uniform(0.6, 1.6)
    intervals = np.abs(rng.normal(base, base * 0.35, size=n_keys))
    return {
        "text": text,
        "backspace_count": int(rng.integers(*cfg["backspace"])),
        "keydown_times": np.cumsum(intervals).tolist(),
        "response_latency_s": float(rng.uniform(*cfg["latency"])),
        "is_followup": bool(rng.random() < 0.3),
        "followup_depth": int(rng.integers(0, 3)),
        "hour_of_day": int(rng.integers(7, 24)),
    }


def main(n_per_regime: int = 30, seed: int = 7) -> None:
    rng = np.random.default_rng(seed)
    records = [_make_record(r, rng) for r in TEMPLATES for _ in range(n_per_regime)]
    random.Random(seed).shuffle(records)
    print(f"Generati {len(records)} turni sintetici (seed={seed})")

    params = init_params(seed=1)
    prima = run_sanity_checks(params, verbose=False)
    print(f"Sanity check PRIMA (modello vergine): {prima * 100:.0f}%")

    for rec in records:
        tf = text_features(rec["text"])
        kf = keystroke_features(
            rec["keydown_times"],
            backspace_count=rec["backspace_count"],
            personal_baseline=params.personal_typing_baseline(),
        )
        inf = interaction_features(
            rec["response_latency_s"],
            rec["is_followup"],
            rec["followup_depth"],
            rec["hour_of_day"],
        )
        u = build_feature_vector(tf, kf, inf)
        engine_model.step(params, u, update=True, learn_rate_scale=1.0)

    dopo = run_sanity_checks(params, verbose=True)
    print(f"Sanity check DOPO: {dopo * 100:.0f}%  (prima: {prima * 100:.0f}%)")

    if dopo < SOGLIA_SICUREZZA:
        print(
            f"[ATTENZIONE] {dopo * 100:.0f}% < soglia {SOGLIA_SICUREZZA * 100:.0f}%: "
            f"asset NON salvato (i nuovi profili useranno il modello vergine)."
        )
        sys.exit(1)

    engine_model.reset_state(params)  # salva lo stato al baseline appreso
    _ASSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _ASSET_PATH.open("w", encoding="utf-8") as f:
        json.dump(params.to_dict(), f, indent=1)
    print(f"Parametri pre-allenati salvati in: {_ASSET_PATH}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    s = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    main(n_per_regime=n, seed=s)
