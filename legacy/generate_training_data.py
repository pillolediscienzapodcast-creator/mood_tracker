# -*- coding: utf-8 -*-
"""
Genera un dataset sintetico di turni per il pre-training iniziale di NOEMA,
usando frasi italiane variate: forme dirette, negazioni, intensificatori,
emoji, forme miste. Copre le 8 emozioni di base del modello.

Il campo "regime" e' presente SOLO per riferimento umano / diagnostica: il
modello NON lo legge mai — l'apprendimento resta interamente
auto-supervisionato, guidato dall'errore di predizione (vedi noema.py).

Uso:
    python3 generate_training_data.py [n_per_regime] [output.jsonl] [seed]
"""
import sys
import json
import random
import numpy as np

SEED = 7

TEMPLATES = {
    "gioia": {
        "testi": [
            "Sono felice e contento, che bella giornata",
            "Grazie mille, sono davvero entusiasta del risultato!",
            "Che fantastico regalo, sono felicissimo 😊",
            "Oggi mi sento davvero allegro e soddisfatto",
            "Non potrei essere piu' felice di cosi'",
        ],
        "backspace": (0, 2), "n_keys": (30, 60), "base_interval": 0.12, "latency": (2, 6),
    },
    "fiducia": {
        "testi": [
            "Sono sereno e rilassato, tutto va bene",
            "Mi fido di questo processo, andra' tutto bene",
            "Va tutto tranquillo, nessuna fretta",
            "Sono abbastanza sicuro che funzionera'",
            "Mi sento calmo e in controllo della situazione",
        ],
        "backspace": (0, 1), "n_keys": (25, 50), "base_interval": 0.20, "latency": (5, 12),
    },
    "paura": {
        "testi": [
            "Ho paura, sono molto ansioso e nervoso",
            "Sono preoccupato, non so se andra' tutto bene",
            "Mi sento in ansia, ho il panico per la scadenza",
            "Sono terrorizzato all'idea di sbagliare tutto 😱",
            "Non riesco a stare tranquillo, sono molto agitato",
        ],
        "backspace": (2, 6), "n_keys": (25, 50), "base_interval": 0.13, "latency": (2, 6),
    },
    "sorpresa": {
        "testi": [
            "Non me lo aspettavo, che sorpresa incredibile",
            "Wow, non ci posso credere, sono senza parole",
            "Che notizia inaspettata, sono davvero stupito",
            "Non avrei mai immaginato una cosa simile",
            "Incredibile, questo risultato mi ha scioccato",
        ],
        "backspace": (1, 4), "n_keys": (25, 55), "base_interval": 0.10, "latency": (1, 4),
    },
    "tristezza": {
        "testi": [
            "Sono triste e stanco, che brutta giornata",
            "Mi sento giu', non ho voglia di fare niente oggi",
            "Sono tristissimo, mi sento malissimo oggi 😢",
            "Non sono per niente felice di questa situazione",
            "E' stata una giornata pesante, sono esausto",
        ],
        "backspace": (1, 3), "n_keys": (18, 40), "base_interval": 0.28, "latency": (8, 20),
    },
    "disgusto": {
        "testi": [
            "Che schifo, questa cosa mi disgusta profondamente",
            "Trovo tutto questo davvero irritante e fastidioso",
            "E' una situazione insopportabile, mi da' il voltastomaco",
            "Non sopporto proprio questo modo di fare",
            "Che cosa ripugnante, non ci posso pensare",
        ],
        "backspace": (2, 5), "n_keys": (25, 50), "base_interval": 0.11, "latency": (2, 5),
    },
    "rabbia": {
        "testi": [
            "Sono arrabbiato e frustrato, odio questo problema",
            "Sono furioso, questo e' assolutamente inaccettabile!!!",
            "Basta, sono esasperato, voglio una spiegazione ORA",
            "Sono incazzato nero per come sono andate le cose",
            "Non sono affatto contento di questo trattamento 😡",
        ],
        "backspace": (4, 10), "n_keys": (35, 75), "base_interval": 0.08, "latency": (1, 3),
    },
    "anticipazione": {
        "testi": [
            "Non vedo l'ora, sono molto curioso di scoprire cosa succedera'",
            "Sto aspettando con ansia buone notizie",
            "Sono molto curioso di vedere come andra' a finire",
            "Ho grandi speranze per il prossimo progetto",
            "Sto pianificando il futuro con entusiasmo",
        ],
        "backspace": (0, 2), "n_keys": (30, 60), "base_interval": 0.14, "latency": (3, 8),
    },
}


def make_record(regime: str, rng: np.random.Generator) -> dict:
    cfg = TEMPLATES[regime]
    text = str(rng.choice(cfg["testi"]))
    backspace = int(rng.integers(*cfg["backspace"]))
    n_keys = int(rng.integers(*cfg["n_keys"]))
    # Rumore ampio sull'intervallo base, che si sovrappone parzialmente fra
    # regimi: la velocita' di digitazione da sola NON deve essere un segnale
    # affidabile per distinguere le emozioni (persone diverse digitano a
    # velocita' diverse per mille motivi non emotivi) — se il dataset la
    # rende un segnale troppo pulito, il modello impara una scorciatoia che
    # poi generalizza male. Il contenuto lessicale resta il segnale primario.
    base_interval_rumoroso = cfg["base_interval"] * rng.uniform(0.6, 1.6)
    intervals = np.abs(rng.normal(base_interval_rumoroso, base_interval_rumoroso * 0.35, size=n_keys))
    latency = float(rng.uniform(*cfg["latency"]))
    is_followup = bool(rng.random() < 0.3)
    followup_depth = int(rng.integers(0, 3))
    hour = int(rng.integers(7, 24))
    return {
        "regime": regime,  # solo per riferimento umano — il modello non lo usa
        "text": text,
        "backspace_count": backspace,
        "keydown_intervals": [round(float(x), 4) for x in intervals],
        "response_latency_s": round(latency, 2),
        "is_followup": is_followup,
        "followup_depth": followup_depth,
        "hour_of_day": hour,
    }


def main(n_per_regime: int = 30, out_path: str = "training_data.jsonl", seed: int = SEED):
    rng = np.random.default_rng(seed)
    records = []
    for regime in TEMPLATES:
        for _ in range(n_per_regime):
            records.append(make_record(regime, rng))

    random.Random(seed).shuffle(records)
    for i, r in enumerate(records):
        r["turn_id"] = i

    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Scritti {len(records)} turni sintetici in {out_path} (seed={seed})")
    print(f"Emozioni incluse: {', '.join(TEMPLATES.keys())}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    out = sys.argv[2] if len(sys.argv) > 2 else "training_data.jsonl"
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else SEED
    main(n_per_regime=n, out_path=out, seed=seed)
