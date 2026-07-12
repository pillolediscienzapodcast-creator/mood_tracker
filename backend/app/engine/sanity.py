"""Controlli di correttezza semantica.

Batteria di frasi con emozione dominante attesa nota, per verificare che il
modello non abbia imparato associazioni sbagliate (es. contenuti arrabbiati
letti come positivi). Va eseguita in sola inferenza dopo ogni training.
"""

from __future__ import annotations

import copy

from app.engine import model as engine_model
from app.engine.features import (
    build_feature_vector,
    interaction_features,
    keystroke_features,
    text_features,
)
from app.engine.params import ModelParams

SANITY_CHECKS: list[tuple[str, str]] = [
    ("Sono felice e contento, che bella giornata", "gioia"),
    ("Sono sereno e rilassato, tutto va bene", "fiducia"),
    ("Grazie mille, sono davvero entusiasta", "gioia"),
    ("Sono triste e stanco, che brutta giornata", "tristezza"),
    ("Sono arrabbiato e frustrato, odio questo problema", "rabbia"),
    ("Ho paura, sono molto ansioso e nervoso", "paura"),
    ("Che schifo, questa cosa mi disgusta profondamente", "disgusto"),
    ("Non me lo aspettavo, che sorpresa incredibile", "sorpresa"),
    ("Non vedo l'ora, sono molto curioso di scoprire cosa succedera'", "anticipazione"),
    ("Non sono per niente felice di questa situazione", "tristezza"),
    ("Sono tristissimo, mi sento malissimo oggi", "tristezza"),
    ("Sono furioso, questo e' assolutamente inaccettabile!!!", "rabbia"),
]


def run_sanity_checks(p: ModelParams, verbose: bool = False) -> float:
    """Esegue la batteria in sola inferenza su una COPIA dei parametri (non
    altera lo stato reale). Ogni frase parte pulita dal baseline z0.
    Ritorna la frazione di test superati."""
    corretti = 0
    for testo, atteso in SANITY_CHECKS:
        prova = copy.deepcopy(p)
        prova.z = prova.z0.copy()
        tf = text_features(testo)
        kf = keystroke_features([0.18, 0.35, 0.52, 0.71, 0.90])  # cadenza neutra
        inf = interaction_features(5.0, False, 0, 12)
        u = build_feature_vector(tf, kf, inf)
        result = engine_model.step(prova, u, update=False)
        ottenuto = result.dominant[0][0] if result.dominant else "nessuna"
        ok = ottenuto == atteso
        corretti += ok
        if verbose:
            simbolo = "OK " if ok else "XXX"
            riga = f"  {simbolo} atteso={atteso:14s} ottenuto={ottenuto:14s}"
            print(f'{riga}  "{testo[:40]}"')
    frazione = corretti / len(SANITY_CHECKS)
    if verbose:
        print(f"  -> {corretti}/{len(SANITY_CHECKS)} corretti ({frazione * 100:.0f}%)")
    return frazione
