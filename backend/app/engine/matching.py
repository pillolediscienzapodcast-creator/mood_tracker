"""Riconoscimento di parole nel lessico, inclusa la scrittura non standard.

La messaggistica reale scrive le parole (soprattutto quelle emotive forti)
in modi che una corrispondenza esatta non riconoscerebbe mai: lettere
ripetute per enfasi, leet ("c4zzo"), "k" al posto di "c", censure con
asterischi, forme flesse non elencate. Questo modulo prova una cascata di
normalizzazioni, dalla piu' precisa alla meno precisa.
"""

from __future__ import annotations

import re

from app.engine.lexicon import LESSICO, PAROLE_CENSURABILI

# Sostituzioni leet numero -> lettera.
_LEET_MAP = str.maketrans(
    {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b"}
)
_CENSURA_CHARS = set("*#•×")

# Stemmer italiano (Snowball via nltk): puramente algoritmico, nessun
# download di dati. Se nltk non e' disponibile il sistema funziona comunque
# senza il fallback di stemming (solo corrispondenza esatta + normalizzazioni).
try:
    from nltk.stem.snowball import SnowballStemmer

    _STEMMER = SnowballStemmer("italian")
except ImportError:  # pragma: no cover - dipende dall'ambiente
    _STEMMER = None


def collassa_ripetute(s: str) -> str:
    """'grazieee' -> 'grazie', 'nooo' -> 'no': lettere ripetute 3+ volte
    (enfasi tipica della messaggistica) collassate a una sola."""
    return re.sub(r"(.)\1{2,}", r"\1", s)


def normalizza_leet(s: str) -> str:
    return s.translate(_LEET_MAP)


def _costruisci_indice_stem() -> dict[str, dict[str, float]]:
    """Indice radice(stem) -> emozioni, costruito UNA VOLTA dal lessico.
    Riconosce forme flesse non elencate (coniugazioni, plurali...)
    riconducendole alla radice di una parola gia' presente. Quando piu'
    parole con emozioni diverse condividono la stessa radice, i pesi
    vengono mediati (piu' prudente che scegliere arbitrariamente)."""
    if _STEMMER is None:
        return {}
    indice: dict[str, dict[str, float]] = {}
    conteggi: dict[str, int] = {}
    for parola, entry in LESSICO.items():
        stem = _STEMMER.stem(parola)
        indice.setdefault(stem, {})
        conteggi[stem] = conteggi.get(stem, 0) + 1
        for emo, peso in entry.items():
            indice[stem][emo] = indice[stem].get(emo, 0.0) + peso
    for stem, pesi in indice.items():
        n = conteggi[stem]
        indice[stem] = {emo: peso / n for emo, peso in pesi.items()}
    return indice


_INDICE_STEM = _costruisci_indice_stem()


def trova_nel_lessico(tok: str) -> dict[str, float] | None:
    """Cerca un token nel lessico provando, in ordine di precisione
    decrescente: esatto -> ripetute collassate -> leet -> 'k'->'c' ->
    jolly per censure -> radice morfologica (stemming). Ritorna il
    dizionario {emozione: peso} o None se nessuna corrispondenza."""
    if tok in LESSICO:
        return LESSICO[tok]

    collassato = collassa_ripetute(tok)
    if collassato in LESSICO:
        return LESSICO[collassato]

    leet = normalizza_leet(collassato)
    if leet in LESSICO:
        return LESSICO[leet]

    con_c = leet.replace("k", "c")
    if con_c in LESSICO:
        return LESSICO[con_c]

    if any(c in _CENSURA_CHARS for c in tok):
        pattern = (
            "^"
            + "".join("." if c in _CENSURA_CHARS else re.escape(c) for c in tok)
            + "$"
        )
        try:
            regex = re.compile(pattern)
        except re.error:
            return None
        candidati = [k for k in LESSICO if len(k) == len(tok) and regex.match(k)]
        if len(candidati) == 1:
            return LESSICO[candidati[0]]
        if len(candidati) > 1:
            censurabili = [k for k in candidati if k in PAROLE_CENSURABILI]
            if len(censurabili) == 1:
                return LESSICO[censurabili[0]]

    # Ultimo tentativo, meno preciso: radice morfologica. Lo stemming puo'
    # occasionalmente unificare parole diverse per significato.
    if _STEMMER is not None and len(tok) >= 4:
        stem = _STEMMER.stem(con_c if con_c != leet else leet)
        if stem in _INDICE_STEM:
            return _INDICE_STEM[stem]

    return None
