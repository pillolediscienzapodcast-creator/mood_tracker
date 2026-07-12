"""Generazione della descrizione testuale italiana dello stato emotivo.

Traduce lo stato numerico (8 intensita' + PAD + confidenza) in una frase
italiana che riflette le emozioni realmente dominanti, la loro intensita' e
la confidenza della stima — con hedging esplicito quando la confidenza e'
bassa o quando nessuna parola del testo era nel lessico.
"""

from __future__ import annotations


def _qualificatore(x: float) -> str:
    """x = intensita' sigmoide (0.5=neutro). Le soglie sono calibrate sul
    range realistico di un singolo turno (spinta modesta sopra 0.5)."""
    if x < 0.55:
        return "lieve"
    if x < 0.62:
        return "moderata"
    if x < 0.72:
        return "marcata"
    return "molto marcata"


def _confidenza_testo(c: float) -> str:
    if c >= 0.65:
        return "buona"
    if c >= 0.45:
        return "moderata"
    return "bassa"


def genera_descrizione(
    dominant: list[tuple[str, float]],
    pad,
    confidence: float,
    nessuna_parola_riconosciuta: bool = False,
) -> str:
    v, a, d = (float(pad[0]), float(pad[1]), float(pad[2]))
    conf_txt = _confidenza_testo(confidence)

    if not dominant:
        corpo = (
            "Nessuna emozione specifica risulta chiaramente dominante: "
            "il quadro appare sostanzialmente neutro."
        )
    elif len(dominant) == 1:
        nome, inten = dominant[0]
        corpo = (
            f"Emozione dominante: {nome} "
            f"({_qualificatore(inten)}, intensita' {inten:.2f})."
        )
    else:
        (n1, i1), (n2, i2) = dominant[0], dominant[1]
        corpo = (
            f"Emozioni dominanti: {n1} ({_qualificatore(i1)}, {i1:.2f}) "
            f"insieme a {n2} ({_qualificatore(i2)}, {i2:.2f})."
        )

    riassunto_pad = (
        f"Sintesi valenza/attivazione/controllo: V={v:+.2f}, A={a:+.2f}, D={d:+.2f}."
    )
    testo = (
        f"{corpo} {riassunto_pad} "
        f"Confidenza della stima: {conf_txt} ({confidence:.2f}/1). "
    )

    if nessuna_parola_riconosciuta:
        testo += (
            "Nessuna parola di questo messaggio e' presente nel lessico emotivo: "
            "la stima si basa solo su tempi di digitazione e altri segnali indiretti, "
            "non sul contenuto — e' normale che sia poco informativa in un caso cosi'. "
        )
    elif confidence < 0.45:
        testo += (
            "Con una confidenza cosi' bassa questa lettura va considerata indicativa e "
            "provvisoria, non affidabile in senso stretto. "
        )

    testo += (
        "Nota: inferenza automatica da proxy comportamentali "
        "(testo, tempi di digitazione), non una diagnosi ne' una lettura "
        "certa dello stato reale della persona."
    )
    return testo
