# -*- coding: utf-8 -*-
"""
NOEMA v0.4 — Non-neural Online Emotional Manifold Adaptation
================================================================

Modello matematico per la stima e il tracciamento continuo dello stato
emotivo a partire da segnali comportamentali (testo italiano, dinamica di
digitazione, metadati di interazione), con personalizzazione continua via
feedback umano.

COSA E' e COSA NON E':
- E' un sistema dinamico stocastico multi-parametro con adattamento online
  (Recursive Least Squares + discesa a gradiente con leakage), ispirato a
  teoria del controllo adattivo, filtraggio bayesiano e predictive coding.
  NON contiene reti neurali artificiali, non fa backpropagation, non e'
  stato pre-addestrato su corpora enormi.
- E' una combinazione originale di tecniche esistenti applicata a questo
  problema specifico. Non e' "matematica mai vista prima nell'universo" —
  nessuno puo' onestamente garantirlo senza una revisione sistematica
  della letteratura — ma la combinazione e l'architettura risultante non
  sono standard.
- E' "intelligenza artificiale" nel senso ampio/storico del termine
  (sistemi adattivi che modificano il proprio comportamento in base ai
  dati — cibernetica, controllo adattivo, filtraggio bayesiano sono
  storicamente parte dell'AI). NON e' deep learning, non e' un LLM: e'
  un'alternativa deliberata a quello, non un sinonimo.
- E' un prototipo di ricerca. Non e' stato validato su dati umani reali
  con misure di riferimento indipendenti (vedi documento teorico, §6).
  Nessuna quantita' di ingegneria del codice sostituisce quella
  validazione — la fornisce solo l'evidenza empirica su persone reali.

ATTENZIONE — USO RESPONSABILE
------------------------------
Raccoglie dati comportamentali sensibili. Va usato solo con il consenso
informato ed esplicito della persona monitorata. Non va mai usato per
sorvegliare altre persone a loro insaputa, ne' per profilarle a partire
da contenuti pubblici (social, LinkedIn, pubblicazioni) senza il loro
consenso specifico a QUESTO uso.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from collections import deque
import datetime
import json
import re

from lessico_italiano import (
    EMOTIONS, LESSICO, NEGATORI, INTENSIFICATORI, DIMINUTORI, EMOJI,
    PRONOMI_SE, PRONOMI_ALTRI, PAD_COORDS, PAROLE_CENSURABILI, FRASI,
)

try:
    from nltk.stem.snowball import SnowballStemmer
    _STEMMER = SnowballStemmer("italian")
except ImportError:
    _STEMMER = None  # se nltk non e' installato, il sistema funziona comunque
                      # senza il fallback di stemming (solo corrispondenza esatta)

N_STATE = len(EMOTIONS)  # 8 emozioni di base (Plutchik)

# Indice radice(stem) -> emozioni, costruito UNA VOLTA dal lessico
# esistente. Permette di riconoscere forme flesse non elencate a mano
# (es. "arrabbiava", "arrabbiarsi", "arrabbieranno" tutte riconducibili
# alla radice di "arrabbiato", gia' nel lessico) senza dover elencare
# ogni coniugazione verbale una per una. Quando piu' parole del lessico
# condividono la stessa radice con emozioni diverse, i pesi vengono
# mediati (non e' garantito che lo stemmer unifichi solo forme
# semanticamente equivalenti — mediare e' piu' prudente che scegliere
# arbitrariamente una delle due).
def _costruisci_indice_stem() -> dict:
    if _STEMMER is None:
        return {}
    indice: dict = {}
    conteggi: dict = {}
    for parola, entry in LESSICO.items():
        stem = _STEMMER.stem(parola)
        if stem not in indice:
            indice[stem] = {}
            conteggi[stem] = 0
        conteggi[stem] += 1
        for emo, peso in entry.items():
            indice[stem][emo] = indice[stem].get(emo, 0.0) + peso
    for stem, pesi in indice.items():
        n = conteggi[stem]
        indice[stem] = {emo: peso / n for emo, peso in pesi.items()}
    return indice


_INDICE_STEM = _costruisci_indice_stem()


# =============================================================================
# 1. SPAZIO DEGLI STATI EMOTIVI
# =============================================================================
# Stato a N_STATE dimensioni, una per ciascuna emozione di base. Lo stato
# "grezzo" z evolve senza vincoli in R^N_STATE; l'intensita' osservabile di
# ciascuna emozione e' sigmoid(alpha*z) in (0,1) — 0 = assente, 1 = massima.
# Valenza/Arousal/Dominanza (PAD) sono DERIVATE come combinazione pesata
# delle intensita' correnti (non sono piu' lo stato primario: sono un
# riassunto a valle, utile per una lettura rapida).

@dataclass
class EmotionalState:
    z: np.ndarray = field(default_factory=lambda: np.zeros(N_STATE))
    alpha: float = 1.0

    @property
    def intensities(self) -> np.ndarray:
        """Intensita' (0,1) di ciascuna delle N_STATE emozioni di base."""
        return 1.0 / (1.0 + np.exp(-np.clip(self.alpha * self.z, -30, 30)))

    @property
    def pad(self) -> np.ndarray:
        """(Valenza, Arousal, Dominanza) derivate come combinazione pesata
        dello SCOSTAMENTO DAL NEUTRO (0.5) delle intensita' correnti,
        secondo le coordinate approssimative PAD_COORDS. Usare
        l'intensita' grezza invece dello scostamento sarebbe un bug: dato
        che il punto neutro di ciascuna delle 8 emozioni e' 0.5 (non 0),
        la sola condizione di riposo (tutte le emozioni a 0.5) produrrebbe
        gia' un PAD fortemente sbilanciato invece che neutro."""
        scostamento = self.intensities - 0.5
        coords = np.array([PAD_COORDS[e] for e in EMOTIONS])  # (N_STATE, 3)
        pad = scostamento @ coords
        return np.clip(pad, -1.0, 1.0)

    def dominanti(self, k: int = 2, soglia: float = 0.515) -> list:
        """Le k emozioni piu' intense al momento, sopra una soglia minima di
        attivazione, come lista di (nome, intensita'), ordinata per
        intensita' decrescente. NOTA: con la sigmoide il punto neutro
        (nessun segnale) e' 0.5, non 0 — la soglia va quindi fissata
        chiaramente SOPRA 0.5, altrimenti rumore casuale intorno al
        neutro verrebbe scambiato per un'emozione presente. Il valore di
        default e' volutamente vicino a 0.5: un singolo turno produce per
        design una spinta modesta (l'inerzia dello stato e' intenzionale,
        vedi documento teorico) — una soglia troppo alta impedirebbe di
        rilevare emozioni reali ma lievi in un solo turno."""
        inten = self.intensities
        idx = np.argsort(-inten)
        risultato = []
        for i in idx[:k]:
            if inten[i] >= soglia:
                risultato.append((EMOTIONS[i], float(inten[i])))
        return risultato


# =============================================================================
# 2. ESTRAZIONE DELLE FEATURE — lingua italiana, dinamica di digitazione,
#    metadati di interazione
# =============================================================================

_LEET_MAP = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b"})
_CENSURA_CHARS = set("*#•×")


def _collassa_ripetute(s: str) -> str:
    """'grazieee' -> 'grazie', 'nooo' -> 'no': lettere ripetute 3+ volte
    (enfasi tipica della messaggistica informale) collassate a una sola."""
    return re.sub(r"(.)\1{2,}", r"\1", s)


def _trova_nel_lessico(tok: str) -> dict | None:
    """
    Cerca 'tok' nel lessico provando, in ordine:
    1. corrispondenza esatta;
    2. lettere ripetute collassate ("grazieee" -> "grazie");
    3. sostituzione leet numero->lettera ("c4zzo" -> "cazzo");
    4. 'k' informale al posto di 'c' ("kazzo" -> "cazzo", "ke" -> "che");
    5. se il token contiene caratteri di censura (* # ecc.), una
       corrispondenza jolly nell'intero lessico ("ca**o" -> "cazzo"),
       accettata SOLO se univoca (un'unica parola di quella lunghezza
       corrisponde) — altrimenti si rischierebbe un match sbagliato.
    Necessario perche' la messaggistica informale reale scrive le parole
    (soprattutto le parolacce) in modi che una tokenizzazione esatta da
    sola non riconoscerebbe mai.
    """
    if tok in LESSICO:
        return LESSICO[tok]

    collassato = _collassa_ripetute(tok)
    if collassato in LESSICO:
        return LESSICO[collassato]

    leet = collassato.translate(_LEET_MAP)
    if leet in LESSICO:
        return LESSICO[leet]

    con_c = leet.replace("k", "c")
    if con_c in LESSICO:
        return LESSICO[con_c]

    if any(c in _CENSURA_CHARS for c in tok):
        pattern = "^" + "".join("." if c in _CENSURA_CHARS else re.escape(c) for c in tok) + "$"
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

    # Ultimo tentativo: radice morfologica (stemming). Riconosce forme
    # flesse non elencate esplicitamente (verbi coniugati, plurali...)
    # riconducendole alla stessa radice di una parola gia' nel lessico.
    # Va per ultimo perche' e' il livello meno preciso: lo stemming puo'
    # occasionalmente unificare parole diverse per significato che
    # condividono solo la forma.
    if _STEMMER is not None and len(tok) >= 4:
        stem = _STEMMER.stem(con_c if con_c != leet else leet)
        if stem in _INDICE_STEM:
            return _INDICE_STEM[stem]

    return None


def text_features(text: str) -> dict:
    """
    Estrae feature linguistiche italiane dal testo, gestendo:
    negazione (finestra di 3 token), intensificatori/diminutori, suffissi
    superlativi (-issimo), emoji/emoticon, rapporto di auto-focus
    (pronomi prima persona vs plurale/altri), enfasi da lettere ripetute,
    e parole scritte in modo non standard (leet, censura, ripetizioni) —
    vedi _trova_nel_lessico().
    """
    text_lower = text.lower()
    # Include anche cifre e simboli di censura comuni nel token, non solo
    # lettere: altrimenti "ca**o" o "c4zzo" verrebbero spezzate ai bordi
    # dei caratteri non alfabetici, in due frammenti irriconoscibili,
    # PRIMA ancora di arrivare alla ricerca nel lessico.
    tokens = re.findall(r"[a-zàèéìòù0-9*#•]+(?:'[a-zàèéìòù0-9*#•]+)?", text_lower)
    n = len(tokens) or 1

    emo_scores = {e: 0.0 for e in EMOTIONS}
    n_matched = 0

    i = 0
    while i < len(tokens):
        # Prova prima le frasi idiomatiche (dalla piu' lunga alla piu'
        # corta): "non vedo l'ora" deve essere riconosciuta come attesa
        # positiva PRIMA che "non" venga interpretato come negazione
        # della parola successiva — la somma delle parole singole
        # darebbe un risultato sbagliato.
        frase_trovata = None
        frase_lunghezza = 0
        for lunghezza in (4, 3, 2):
            candidata = tuple(tokens[i:i + lunghezza])
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

        tok = tokens[i]
        entry = _trova_nel_lessico(tok)
        if entry is None:
            i += 1
            continue
        # Negazione: finestra solo all'indietro — in italiano la negazione
        # precede quasi sempre la parola che nega ("non sono felice");
        # guardare anche in avanti rischierebbe falsi positivi con
        # negazioni finali non collegate ("sono felice, non e' vero?").
        contesto_prima = [_collassa_ripetute(w).translate(_LEET_MAP) for w in tokens[max(0, i - 3):i]]
        negato = any(w in NEGATORI for w in contesto_prima)

        # Intensificatori/diminutori: finestra BIDIREZIONALE — sono comuni
        # sia prima ("molto felice") che dopo ("felice tantissimo") la
        # parola emotiva in italiano.
        contesto_dopo = [_collassa_ripetute(w).translate(_LEET_MAP) for w in tokens[i + 1:i + 3]]
        finestra_intensita = contesto_prima + contesto_dopo
        moltiplicatore = 1.0
        if any(w in INTENSIFICATORI for w in finestra_intensita):
            moltiplicatore = 1.5
        elif any(w in DIMINUTORI for w in finestra_intensita):
            moltiplicatore = 0.5
        if tok.endswith(("issimo", "issima", "issimi", "issime")):
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

    repeated_chars = len(re.findall(r"(.)\1{2,}", text))

    out = {f"lex_{emo}": emo_scores[emo] for emo in EMOTIONS}
    out.update({
        "sentence_len": n,
        "exclaim_rate": text.count("!") / n,
        "question_rate": text.count("?") / n,
        "ellipsis_rate": text.count("...") / n,
        "caps_word_rate": sum(1 for w in text.split() if w.isupper() and len(w) > 1) / n,
        "self_focus_ratio": self_focus_ratio,
        "repeated_char_rate": repeated_chars / n,
    })
    return out


def keystroke_features(keydown_times: list, backspace_count: int = 0,
                        personal_baseline: dict = None) -> dict:
    """
    Dinamica di digitazione. Se personal_baseline e' fornito (media/std
    storiche di QUESTA persona per typing_speed), la velocita' viene anche
    espressa in unita' relative al proprio ritmo abituale — "veloce"
    ha senso solo relativamente a come scrive di solito quella persona,
    non a una soglia assoluta uguale per tutti.
    """
    if len(keydown_times) < 2:
        return {"typing_speed": 0.0, "rhythm_variability": 0.0,
                "burstiness": 0.0, "error_rate": 0.0, "typing_speed_relative": 0.0}
    intervals = np.diff(np.asarray(keydown_times, dtype=float))
    mu, sigma = float(np.mean(intervals)), float(np.std(intervals))
    speed = 1.0 / (mu + 1e-6)
    variability = sigma / (mu + 1e-6)
    burstiness = (sigma - mu) / (sigma + mu + 1e-6)
    error_rate = backspace_count / max(len(keydown_times), 1)

    speed_relative = 0.0
    if personal_baseline and personal_baseline.get("typing_speed_std", 0) > 1e-6:
        speed_relative = (speed - personal_baseline["typing_speed_mean"]) / personal_baseline["typing_speed_std"]

    return {"typing_speed": speed, "rhythm_variability": variability,
            "burstiness": burstiness, "error_rate": error_rate,
            "typing_speed_relative": float(np.clip(speed_relative, -4, 4))}


def interaction_features(response_latency_s: float, is_followup: bool,
                          followup_depth: int, hour_of_day: int) -> dict:
    circadian_phase = float(np.sin(2 * np.pi * hour_of_day / 24))
    return {
        "response_latency": response_latency_s,
        "is_followup": float(is_followup),
        "followup_depth": followup_depth,
        "circadian_phase": circadian_phase,
    }


FEATURE_ORDER = (
    [f"lex_{e}" for e in EMOTIONS] +
    ["sentence_len", "exclaim_rate", "question_rate", "ellipsis_rate",
     "caps_word_rate", "self_focus_ratio", "repeated_char_rate",
     "typing_speed", "rhythm_variability", "burstiness", "error_rate",
     "typing_speed_relative",
     "response_latency", "is_followup", "followup_depth", "circadian_phase"]
)
N_FEATURES = len(FEATURE_ORDER)  # 8 (lessico) + 7 (testo) + 5 (digitazione) + 4 (interazione) = 24

_FEATURE_SCALE = {
    "sentence_len": 20.0, "exclaim_rate": 1.0, "question_rate": 1.0,
    "ellipsis_rate": 1.0, "caps_word_rate": 1.0, "self_focus_ratio": 1.0,
    "repeated_char_rate": 1.0, "typing_speed": 6.0, "rhythm_variability": 2.0,
    "burstiness": 1.0, "error_rate": 1.0, "typing_speed_relative": 2.0,
    "response_latency": 15.0, "is_followup": 1.0, "followup_depth": 5.0,
    "circadian_phase": 1.0,
    **{f"lex_{e}": 1.0 for e in EMOTIONS},
}

# Centro "neutro" per feature che non hanno un naturale zero=assenza-di-segnale
# (es. una latenza di risposta di 0 secondi non e' "neutra", e' anomala: il
# valore tipico/atteso e' qualche secondo). SENZA centratura, una feature
# sempre positiva e presente ad ogni turno, se collegata nel prior a un solo
# asse emotivo, lo spinge sistematicamente verso l'alto turno dopo turno,
# indipendentemente dal contenuto — esattamente il bug che ha causato un
# collasso del modello su una singola emozione in una versione precedente
# di questo file (vedi il documento teorico). Le feature di enfasi
# (esclamazioni, maiuscole, ripetizioni...) NON vanno centrate: per quelle
# zero=assenza di enfasi e' gia' il neutro corretto.
_FEATURE_CENTER = {
    "sentence_len": 12.0, "typing_speed": 4.0, "rhythm_variability": 0.35,
    "response_latency": 6.0, "is_followup": 0.5, "followup_depth": 1.0,
}


def build_feature_vector(text_f: dict, key_f: dict, inter_f: dict,
                          clip_value: float = 4.0) -> np.ndarray:
    """Costruisce il vettore di feature normalizzato (centrato e scalato),
    con clip di sicurezza contro input anomali o malformati."""
    d = {**text_f, **key_f, **inter_f}
    raw = np.array(
        [(d.get(k, 0.0) - _FEATURE_CENTER.get(k, 0.0)) / _FEATURE_SCALE.get(k, 1.0)
         for k in FEATURE_ORDER],
        dtype=float,
    )
    if not np.all(np.isfinite(raw)):
        raw = np.nan_to_num(raw, nan=0.0, posinf=clip_value, neginf=-clip_value)
    return np.clip(raw, -clip_value, clip_value)


# =============================================================================
# 3. NUCLEO ADATTIVO
# =============================================================================

class NoemaModel:
    """
    Equazione di stato (discretizzazione di Eulero-Maruyama):
        z_{t+1} = z_t + dt * [ -K (z_t - z0) + B u_t ] + rumore
    Predizione generativa (predictive coding):
        u_pred_t = C * sigmoid(alpha * z_{t+1})
        errore_t = u_t - u_pred_t
    C e' stimata con Recursive Least Squares (RLS); B con discesa a
    gradiente a tasso decrescente + leakage; K, z0, alpha si auto-regolano.
    In piu' rispetto alle versioni precedenti: stato a N_STATE=8 dimensioni
    (emozioni di base, non solo PAD), normalizzazione online delle feature
    per-utente, e un meccanismo di correzione supervisionata da feedback
    umano (vedi apply_feedback / consolidate_feedback).
    """

    MODEL_VERSION = "0.4.0"

    def __init__(self, n_features: int = N_FEATURES, dt: float = 0.9,
                 seed: int = 0, K_scale: float = 0.35, rls_lambda: float = 0.995,
                 P0_scale: float = 12.0, eta_B0: float = 0.02, tau_B: float = 220.0,
                 leak_B: float = 0.10, leak_z0: float = 0.7,
                 eta_K: float = 0.02, eta_alpha: float = 0.03,
                 target_variance: float = 0.05, consolidation_every: int = 5):
        rng = np.random.default_rng(seed)
        self.dt = dt
        self.n_features = n_features
        self.state = EmotionalState(z=np.zeros(N_STATE))

        self.K = np.eye(N_STATE) * K_scale
        self.z0 = np.zeros(N_STATE)
        self.B = self._init_B(n_features, rng)
        self.B_prior = self.B.copy()
        self.B_intenzionale = self._maschera_connessioni_intenzionali(n_features)
        self.C = rng.normal(0, 0.05, size=(n_features, N_STATE))

        self.P = np.eye(N_STATE) * P0_scale
        self.rls_lambda = rls_lambda

        self.eta_B0 = eta_B0
        self.tau_B = tau_B
        self._t = 0

        self.leak_B = leak_B
        self.leak_z0 = leak_z0
        self.eta_K = eta_K
        self.eta_alpha = eta_alpha

        self._recent_e = deque(maxlen=40)
        self.target_variance = target_variance

        # --- Normalizzazione online per-utente (Welford) ---
        # Media e varianza correnti delle feature GREZZE (prima della
        # scala fissa _FEATURE_SCALE), specifiche per la persona
        # monitorata: "digita veloce" ha senso relativamente al proprio
        # ritmo abituale, non a una soglia identica per chiunque.
        self._feat_mean = np.zeros(n_features)
        self._feat_M2 = np.zeros(n_features)
        self._feat_n = 0

        # --- Feedback supervisionato ---
        self.consolidation_every = consolidation_every
        self._feedback_buffer: list = []
        self._feedback_count = 0
        self._last_u: np.ndarray = None

        self.history: list = []

    @staticmethod
    def _init_B(n_features: int, rng: np.random.Generator) -> np.ndarray:
        """Prior psicologicamente motivato: ogni feature lessicale
        'lex_X' punta direttamente all'asse emotivo X; le feature
        paralinguistiche di attivazione (punteggiatura enfatica, errori
        di digitazione, velocita', variabilita' del ritmo) alimentano
        debolmente le emozioni ad alta attivazione (rabbia, paura,
        sorpresa). Il modello NON resta vincolato a questo prior: lo
        aggiorna comunque nel tempo in base ai propri errori di
        predizione (vedi step())."""
        B = rng.normal(0, 0.02, size=(N_STATE, n_features))
        for i, feat_name in enumerate(FEATURE_ORDER):
            if feat_name.startswith("lex_"):
                emo = feat_name[4:]
                j = EMOTIONS.index(emo)
                B[j, i] += 0.5
        for feat_name, peso in [("exclaim_rate", 0.15), ("repeated_char_rate", 0.10),
                                  ("error_rate", 0.15), ("typing_speed_relative", 0.10),
                                  ("rhythm_variability", 0.08)]:
            if feat_name in FEATURE_ORDER:
                i = FEATURE_ORDER.index(feat_name)
                for emo in ("rabbia", "paura", "sorpresa"):
                    B[EMOTIONS.index(emo), i] += peso / 3.0
        if "response_latency" in FEATURE_ORDER:
            i = FEATURE_ORDER.index("response_latency")
            B[EMOTIONS.index("tristezza"), i] += 0.10
        return B

    @staticmethod
    def _maschera_connessioni_intenzionali(n_features: int) -> np.ndarray:
        """Maschera (N_STATE x n_features) che marca ESPLICITAMENTE quali
        celle di B corrispondono a connessioni deliberate del prior
        psicologico (vedi _init_B), indipendentemente dal valore casuale
        che quella cella ha assunto all'inizializzazione. E' necessaria
        perche' dedurre "intenzionale o no" da una soglia sul valore
        casuale del prior non e' affidabile: il rumore casuale (std 0.02)
        supera occasionalmente qualunque soglia bassa per puro caso,
        lasciando singole celle non protette dal leak rinforzato — bug
        osservato durante lo sviluppo con circadian_phase (vedi documento
        teorico). Le celle marcate 1.0 mantengono il leak normale verso
        il prior; le altre ricevono un leak molto piu' forte."""
        mask = np.zeros((N_STATE, n_features))
        for i, feat_name in enumerate(FEATURE_ORDER):
            if feat_name.startswith("lex_"):
                mask[EMOTIONS.index(feat_name[4:]), i] = 1.0
        for feat_name in ("exclaim_rate", "repeated_char_rate", "error_rate",
                          "typing_speed_relative", "rhythm_variability"):
            if feat_name in FEATURE_ORDER:
                i = FEATURE_ORDER.index(feat_name)
                for emo in ("rabbia", "paura", "sorpresa"):
                    mask[EMOTIONS.index(emo), i] = 1.0
        if "response_latency" in FEATURE_ORDER:
            i = FEATURE_ORDER.index("response_latency")
            mask[EMOTIONS.index("tristezza"), i] = 1.0
        return mask

    # -------------------------------------------------------------------
    # Normalizzazione online per-utente (algoritmo di Welford)
    # -------------------------------------------------------------------
    def _traccia_statistiche(self, u_raw: np.ndarray) -> None:
        """Aggiorna solo le statistiche (media/varianza di Welford) delle
        feature grezze per QUESTO utente, senza trasformare il vettore
        usato dalla dinamica. Le statistiche alimentano
        personal_typing_baseline() (usato per calcolare la feature dedicata
        typing_speed_relative), non l'intero vettore di feature — una
        prima versione trasformava l'intero vettore ad ogni turno, ma
        questo creava un bersaglio di predizione "in movimento" per la RLS
        (le statistiche cambiano ad ogni turno) e destabilizzava il
        training. Personalizzare tramite una feature dedicata invece che
        deformando l'intero spazio di input e' piu' sicuro."""
        self._feat_n += 1
        delta = u_raw - self._feat_mean
        self._feat_mean += delta / self._feat_n
        delta2 = u_raw - self._feat_mean
        self._feat_M2 += delta * delta2

    def personal_typing_baseline(self) -> dict:
        """Espone la baseline di velocita' di digitazione appresa per
        questo utente, riconvertita in unita' grezze (tasti/secondo):
        le statistiche interne (_feat_mean/_feat_M2) sono tracciate nello
        spazio delle feature gia' centrato e scalato, quindi vanno
        riportate indietro prima di essere confrontate con una velocita'
        grezza in keystroke_features() — confrontare direttamente le due
        unita' diverse produceva sempre un valore estremo, causa di un
        bug di deriva osservato durante lo sviluppo (vedi documento
        teorico)."""
        idx = FEATURE_ORDER.index("typing_speed")
        if self._feat_n < 10:
            return {}
        std_scalato = float(np.sqrt(self._feat_M2[idx] / max(self._feat_n - 1, 1)))
        media_scalata = float(self._feat_mean[idx])
        scala = _FEATURE_SCALE["typing_speed"]
        centro = _FEATURE_CENTER.get("typing_speed", 0.0)
        return {
            "typing_speed_mean": media_scalata * scala + centro,
            "typing_speed_std": max(std_scalato * scala, 1e-6),
        }

    # -------------------------------------------------------------------
    # 3.1 Passo online
    # -------------------------------------------------------------------
    def step(self, u_t: np.ndarray, update: bool = True,
              learn_rate_scale: float = 1.0) -> EmotionalState:
        """
        update=True (default): passo normale, aggiorna sia lo stato che i
        parametri appresi.
        update=False: modalita' "sola inferenza" — calcola una stima senza
        toccare i parametri. Utile per controlli di qualita' (sanity
        check) o query che non devono influenzare l'apprendimento futuro.

        learn_rate_scale: fattore che scala SOLO l'apprendimento dei
        parametri (B, C, K, z0), non il tracciamento dello stato (che
        resta sempre pienamente reattivo). Durante il training batch
        (fit()) resta 1.0: li' i dati sono sintetici, bilanciati, e il
        gate di sicurezza (sanity check) verifica il risultato prima di
        salvare. Durante l'uso live turno-per-turno (ingest_turn()) va
        invece ridotto: testo reale imprevisto, fuori dalla distribuzione
        sintetica di training, puo' produrre errori di predizione grandi
        che — con il pieno tasso di apprendimento — generano correzioni
        sproporzionate e un drift instabile nel giro di pochi turni (bug
        osservato e corretto durante lo sviluppo: vedi il documento
        teorico). La vera personalizzazione in uso live e' delegata
        soprattutto al feedback umano esplicito (apply_feedback /
        consolidate_feedback), che e' supervisionato e quindi piu'
        affidabile di una correzione auto-referenziale non verificata.
        """
        z, alpha = self.state.z, self.state.alpha

        if update:
            self._traccia_statistiche(u_t)
            self._t += 1
            self._last_u = u_t.copy()

        u_norm_pers = u_t

        drift = -self.K @ (z - self.z0) + self.B @ u_norm_pers
        z_pred = z + self.dt * drift
        e_pred = 1.0 / (1.0 + np.exp(-np.clip(alpha * z_pred, -30, 30)))
        u_pred = self.C @ e_pred
        error = u_norm_pers - u_pred

        if update:
            Px = self.P @ e_pred
            denom = self.rls_lambda + float(e_pred @ Px) + 1e-8
            k_gain = Px / denom
            self.C += learn_rate_scale * np.outer(error, k_gain)
            self.P = (self.P - np.outer(k_gain, Px)) / self.rls_lambda
            self.P = 0.5 * (self.P + self.P.T)

            eta_B_t = learn_rate_scale * self.eta_B0 / (1.0 + self._t / self.tau_B)
            u_norm_sq = float(np.dot(u_norm_pers, u_norm_pers)) + 1e-4
            grad_B = np.outer(self.C.T @ error, u_norm_pers) / u_norm_sq
            # Leak differenziato: le connessioni DELIBERATE del prior (lessico
            # -> asse emotivo, cluster di attivazione paralinguistica) hanno
            # un valore assoluto grande e mantengono il leak normale; le
            # connessioni NON previste dal prior (inizializzate solo con
            # rumore casuale ~0.02) vengono vincolate con un leak molto piu'
            # forte. Senza questa distinzione, l'adattamento non supervisionato
            # puo' sviluppare pesi spuri grandi su feature senza relazione
            # concettuale con l'emozione (osservato con circadian_phase che
            # aveva sviluppato un peso di -0.42 su "sorpresa" durante il
            # training — causa di un bug di deriva scoperto durante lo
            # sviluppo, vedi documento teorico).
            fuori_dal_prior = 1.0 - self.B_intenzionale
            leak_effettivo = self.leak_B * (1.0 + 8.0 * fuori_dal_prior)
            self.B += eta_B_t * grad_B - leak_effettivo * eta_B_t * (self.B - self.B_prior)

            volatility = np.abs(z_pred - z)
            self.K += learn_rate_scale * self.eta_K * (np.diag(volatility) - self.K) * 0.1
            self.K = np.clip(self.K, 0.01, 1.0) * np.eye(N_STATE)

            # Il leak su z0 tira ogni asse verso la MEDIA di tutti gli assi
            # (non solo verso zero): previene strutturalmente che un
            # singolo asse "scappi" dal gruppo per una deriva sistematica
            # cumulata su molti turni (qualunque ne sia la causa specifica),
            # mantenendo pero' le differenze RELATIVE fra assi che
            # rappresentano una vera personalizzazione del baseline.
            z0_media = float(np.mean(self.z0))
            self.z0 += learn_rate_scale * (0.01 * (z_pred - self.z0) - self.leak_z0 * (self.z0 - z0_media))

        self.state.z = z_pred
        if update:
            self._recent_e.append(self.state.intensities.copy())
            if len(self._recent_e) >= 10:
                var_obs = float(np.mean(np.var(np.array(self._recent_e), axis=0)))
                self.state.alpha += self.eta_alpha * (self.target_variance - var_obs)
                self.state.alpha = float(np.clip(self.state.alpha, 0.2, 5.0))

            self.history.append({
                "intensities": self.state.intensities.copy(),
                "pad": self.state.pad.copy(),
                "alpha": self.state.alpha,
                "pred_error_norm": float(np.linalg.norm(error)),
                "confidence": self._confidence(error),
            })
        return self.state

    def _confidence(self, error: np.ndarray) -> float:
        """Confidenza combinata (0-1): errore di predizione istantaneo +
        incertezza residua sui parametri (traccia della precisione RLS)."""
        conf_errore = 1.0 / (1.0 + float(np.linalg.norm(error)))
        conf_parametri = 1.0 / (1.0 + float(np.trace(self.P)) / N_STATE)
        return float(np.clip(0.5 * conf_errore + 0.5 * conf_parametri, 0.0, 1.0))

    # -------------------------------------------------------------------
    # 3.2 Training esplicito su batch
    # -------------------------------------------------------------------
    def fit(self, records: list, verbose: bool = False) -> "NoemaModel":
        n = len(records)
        for i, rec in enumerate(records):
            keydown_times = np.cumsum(rec.get("keydown_intervals", [])).tolist()
            tf = text_features(rec.get("text", ""))
            kf = keystroke_features(keydown_times, backspace_count=rec.get("backspace_count", 0),
                                     personal_baseline=self.personal_typing_baseline())
            inf = interaction_features(
                rec.get("response_latency_s", 5.0), rec.get("is_followup", False),
                rec.get("followup_depth", 0), rec.get("hour_of_day", 12),
            )
            u = build_feature_vector(tf, kf, inf)
            state = self.step(u)
            if verbose and (i % max(1, n // 10) == 0 or i == n - 1):
                dom = state.dominanti(k=1)
                lbl = dom[0][0] if dom else "neutro"
                err = self.history[-1]["pred_error_norm"]
                print(f"[{i+1:4d}/{n}] emozione dominante={lbl:14s} "
                      f"alpha={state.alpha:.3f} errore_pred={err:.3f}")
        return self

    # -------------------------------------------------------------------
    # 3.3 Feedback supervisionato e consolidamento periodico
    # -------------------------------------------------------------------
    def apply_feedback(self, corretto: bool, emozione_corretta: str = None,
                        intensita: float = 0.75, gain: float = 0.4) -> None:
        """
        Applica una correzione supervisionata basata sul feedback umano
        sull'ULTIMA stima prodotta da step()/ingest_turn().

        corretto=True  -> conferma leggera dello stato corrente.
        corretto=False -> richiede emozione_corretta (uno dei nomi in
            EMOTIONS): lo stato viene spostato verso quel target con
            guadagno 'gain' (e' un'osservazione che corregge la stima
            corrente, non un reset completo).

        Il turno viene anche salvato in un buffer per il consolidamento
        periodico (vedi consolidate_feedback()), che avviene in automatico
        ogni 'consolidation_every' feedback.
        """
        if self._last_u is None:
            raise RuntimeError("Nessun turno precedente su cui applicare il feedback: "
                                "chiama step()/ingest_turn() almeno una volta prima.")
        if not corretto and emozione_corretta not in EMOTIONS:
            raise ValueError(f"emozione_corretta deve essere una di {EMOTIONS}, "
                              f"ricevuto: {emozione_corretta!r}")

        target = self.state.z.copy()
        if not corretto:
            target = np.zeros(N_STATE)
            j = EMOTIONS.index(emozione_corretta)
            logit = np.log(intensita / (1 - intensita + 1e-6) + 1e-6)
            target[j] = logit / max(self.state.alpha, 1e-3)

        self.state.z = self.state.z + gain * (target - self.state.z)
        self._feedback_buffer.append((self._last_u.copy(), target.copy()))
        self._feedback_count += 1

        esito = "confermato" if corretto else f"corretto verso '{emozione_corretta}'"
        print(f"[NOEMA] Feedback registrato: {esito}. "
              f"Buffer di consolidamento: {len(self._feedback_buffer)}/{self.consolidation_every}")

        if self._feedback_count % self.consolidation_every == 0:
            self.consolidate_feedback()

    def consolidate_feedback(self) -> None:
        """
        Rielabora i feedback raccolti finora, aggiornando B e C usando i
        target FORNITI DALL'UMANO al posto dell'auto-predizione: una
        correzione supervisionata invece che auto-supervisionata, con un
        peso maggiore di un normale passo online.

        Frequenza di default: ogni 5 feedback. E' una dimensione di
        mini-batch comune nell'apprendimento online — abbastanza piccola
        da restare reattiva a un utente nuovo, abbastanza grande da
        mediare il rumore di un singolo giudizio umano (un feedback isolato
        potrebbe essere lui stesso impreciso).
        """
        if not self._feedback_buffer:
            return
        print(f"\n[NOEMA] Consolidamento: rielaboro {len(self._feedback_buffer)} "
              f"feedback per rinforzare i parametri...")
        for u, target in self._feedback_buffer:
            e_target = 1.0 / (1.0 + np.exp(-np.clip(self.state.alpha * target, -30, 30)))
            u_pred = self.C @ e_target
            error = u - u_pred

            Px = self.P @ e_target
            denom = self.rls_lambda + float(e_target @ Px) + 1e-8
            k_gain = Px / denom
            self.C += 1.5 * np.outer(error, k_gain)

            grad_B = np.outer(self.C.T @ error, u) / (float(np.dot(u, u)) + 1e-4)
            self.B += 0.08 * grad_B - self.leak_B * 0.08 * (self.B - self.B_prior)

        print(f"[NOEMA] Consolidamento completato: {len(self._feedback_buffer)} "
              f"correzioni integrate nei parametri.\n")
        self._feedback_buffer.clear()

    # -------------------------------------------------------------------
    # 3.4 Persistenza
    # -------------------------------------------------------------------
    def save_params(self, path: str) -> None:
        payload = {
            "model_version": self.MODEL_VERSION,
            "saved_at": datetime.datetime.now().isoformat(),
            "n_turns_trained": self._t,
            "K": self.K.tolist(), "z0": self.z0.tolist(),
            "B": self.B.tolist(), "B_prior": self.B_prior.tolist(), "C": self.C.tolist(),
            "P": self.P.tolist(), "rls_lambda": self.rls_lambda,
            "alpha": self.state.alpha, "z": self.state.z.tolist(),
            "eta_B0": self.eta_B0, "tau_B": self.tau_B, "t": self._t,
            "leak_B": self.leak_B, "leak_z0": self.leak_z0,
            "eta_K": self.eta_K, "eta_alpha": self.eta_alpha,
            "target_variance": self.target_variance,
            "feat_mean": self._feat_mean.tolist(), "feat_M2": self._feat_M2.tolist(),
            "feat_n": self._feat_n,
            "consolidation_every": self.consolidation_every,
            "feedback_count": self._feedback_count,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load_params(self, path: str) -> "NoemaModel":
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        file_version = payload.get("model_version", "sconosciuta")
        if file_version != self.MODEL_VERSION:
            print(f"[NOEMA] Attenzione: '{path}' salvato con versione {file_version}, "
                  f"questo codice e' alla versione {self.MODEL_VERSION}. Caricamento "
                  f"forzato: la compatibilita' non e' garantita.")
        self.K = np.array(payload["K"]); self.z0 = np.array(payload["z0"])
        self.B = np.array(payload["B"]); self.B_prior = np.array(payload.get("B_prior", payload["B"]))
        self.C = np.array(payload["C"])
        self.P = np.array(payload.get("P", (np.eye(N_STATE) * 50.0).tolist()))
        self.rls_lambda = payload.get("rls_lambda", self.rls_lambda)
        self.state.alpha = payload["alpha"]; self.state.z = np.array(payload["z"])
        self.eta_B0 = payload.get("eta_B0", self.eta_B0)
        self.tau_B = payload.get("tau_B", self.tau_B)
        self._t = payload.get("t", self._t)
        self.leak_B = payload.get("leak_B", self.leak_B)
        self.leak_z0 = payload.get("leak_z0", self.leak_z0)
        self.eta_K = payload.get("eta_K", self.eta_K)
        self.eta_alpha = payload.get("eta_alpha", self.eta_alpha)
        self.target_variance = payload.get("target_variance", self.target_variance)
        self._feat_mean = np.array(payload.get("feat_mean", self._feat_mean.tolist()))
        self._feat_M2 = np.array(payload.get("feat_M2", self._feat_M2.tolist()))
        self._feat_n = payload.get("feat_n", self._feat_n)
        self.consolidation_every = payload.get("consolidation_every", self.consolidation_every)
        self._feedback_count = payload.get("feedback_count", 0)
        return self

    def reset_state(self) -> None:
        """Riporta lo stato corrente al baseline personale appreso (z0),
        mantenendo i parametri di dinamica gia' calibrati."""
        self.state.z = self.z0.copy()

    def get_diagnostics(self) -> dict:
        e0 = 1.0 / (1.0 + np.exp(-np.clip(self.state.alpha * self.z0, -30, 30)))
        return {
            "model_version": self.MODEL_VERSION,
            "turni_processati": self._t,
            "feedback_ricevuti": self._feedback_count,
            "norma_B": float(np.linalg.norm(self.B)),
            "norma_C": float(np.linalg.norm(self.C)),
            "traccia_P": float(np.trace(self.P)),
            "alpha": float(self.state.alpha),
            "baseline_intensita": [round(float(x), 3) for x in e0],
            "baseline_saturato": bool(np.any(e0 > 0.95) or np.any(e0 < 0.05)),
            "ultimo_errore_predizione": self.history[-1]["pred_error_norm"] if self.history else None,
            "ultima_confidenza": self.history[-1]["confidence"] if self.history else None,
        }


# =============================================================================
# 4. INTERPRETAZIONE TESTUALE IN ITALIANO
# =============================================================================

def _qualificatore(x: float) -> str:
    """x e' un'intensita' sigmoide (0.5=neutro, verso 1=massimo). Un
    singolo turno produce per design una spinta modesta sopra 0.5 (vedi
    dominanti()), quindi le soglie sono calibrate su quel range realistico
    invece che sull'intero 0-1."""
    if x < 0.55:
        return "lieve"
    elif x < 0.62:
        return "moderata"
    elif x < 0.72:
        return "marcata"
    return "molto marcata"


def _confidenza_testo(c: float) -> str:
    if c >= 0.65:
        return "buona"
    elif c >= 0.45:
        return "moderata"
    return "bassa"


def genera_descrizione(state: EmotionalState, confidence: float,
                        nessuna_parola_riconosciuta: bool = False) -> str:
    """
    Traduce lo stato numerico (8 intensita' emotive + confidenza) in una
    descrizione testuale italiana accurata, pensata per il campo 'label'
    dell'output del demone. Riflette le emozioni realmente dominanti
    (non un'etichetta fissa), la loro intensita', e la confidenza della
    stima — con hedging esplicito quando la confidenza e' bassa.

    nessuna_parola_riconosciuta: se True, nessuna parola del testo era nel
    lessico emotivo — la stima si basa solo su altri segnali (tempi di
    digitazione, ecc.). Va segnalato esplicitamente: altrimenti un
    "neutro" per questo motivo e' indistinguibile, per chi legge, da un
    errore del modello.
    """
    dominanti = state.dominanti(k=2)
    v, a, d = state.pad
    conf_txt = _confidenza_testo(confidence)

    if not dominanti:
        corpo = "Nessuna emozione specifica risulta chiaramente dominante: il quadro appare sostanzialmente neutro."
    elif len(dominanti) == 1:
        nome, inten = dominanti[0]
        corpo = f"Emozione dominante: {nome} ({_qualificatore(inten)}, intensita' {inten:.2f})."
    else:
        (n1, i1), (n2, i2) = dominanti
        corpo = (f"Emozioni dominanti: {n1} ({_qualificatore(i1)}, {i1:.2f}) "
                 f"insieme a {n2} ({_qualificatore(i2)}, {i2:.2f}).")

    riassunto_pad = (f"Sintesi valenza/attivazione/controllo: "
                      f"V={v:+.2f}, A={a:+.2f}, D={d:+.2f}.")

    testo = (f"{corpo} {riassunto_pad} Confidenza della stima: {conf_txt} ({confidence:.2f}/1). ")

    if nessuna_parola_riconosciuta:
        testo += ("Nessuna parola di questo messaggio e' presente nel lessico emotivo: "
                   "la stima si basa solo su tempi di digitazione e altri segnali indiretti, "
                   "non sul contenuto — e' normale che sia poco informativa in un caso cosi'. ")
    elif confidence < 0.45:
        testo += ("Con una confidenza cosi' bassa questa lettura va considerata indicativa e "
                   "provvisoria, non affidabile in senso stretto. ")

    testo += ("Nota: inferenza automatica da proxy comportamentali (testo, tempi di digitazione), "
               "non una diagnosi ne' una lettura certa dello stato reale della persona.")
    return testo


# =============================================================================
# 5. CONTROLLI DI CORRETTEZZA SEMANTICA (sanity check)
# =============================================================================
# Batteria di frasi con emozione dominante attesa nota, per verificare che
# il modello non abbia imparato ad associare, ad esempio, contenuti
# arrabbiati a valenza positiva (e' successo in una versione precedente:
# vedi il documento teorico). Va eseguita dopo ogni training prima di
# considerare affidabile una nuova configurazione di parametri.

SANITY_CHECKS = [
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


def run_sanity_checks(model: NoemaModel, verbose: bool = True) -> float:
    """
    Esegue la batteria di controlli di correttezza semantica in modalita'
    sola-inferenza (update=False): NON modifica i parametri del modello,
    misura soltanto se l'emozione dominante prevista corrisponde
    all'attesa. Ogni frase viene valutata INDIPENDENTEMENTE (lo stato
    viene riportato al baseline prima di ciascuna, altrimenti l'esito di
    una frase influenzerebbe quello della successiva). Lo stato reale
    della conversazione in corso (se presente) viene salvato e ripristinato
    alla fine. Ritorna la frazione di test superati.
    """
    stato_salvato = model.state.z.copy()
    corretti = 0
    for testo, atteso in SANITY_CHECKS:
        model.state.z = model.z0.copy()  # ogni prova parte pulita dal baseline
        tf = text_features(testo)
        kf = keystroke_features([0.18, 0.35, 0.52, 0.71, 0.90])  # cadenza neutra realistica
        inf = interaction_features(5.0, False, 0, 12)
        u = build_feature_vector(tf, kf, inf)
        state = model.step(u, update=False)
        dom = state.dominanti(k=1)
        ottenuto = dom[0][0] if dom else "nessuna"
        ok = (ottenuto == atteso)
        corretti += ok
        if verbose:
            simbolo = "OK " if ok else "XXX"
            print(f"  {simbolo} atteso={atteso:14s} ottenuto={ottenuto:14s}  \"{testo[:50]}\"")
    model.state.z = stato_salvato  # ripristina lo stato reale della conversazione
    frazione = corretti / len(SANITY_CHECKS)
    if verbose:
        print(f"  -> {corretti}/{len(SANITY_CHECKS)} corretti ({frazione*100:.0f}%)")
    return frazione


# =============================================================================
# 6. "DEMONE" DI TRACCIAMENTO CONTINUO
# =============================================================================

class NoemaDaemon:
    """
    Consuma eventi (testo, timestamp dei tasti, metadati) e mantiene una
    stima aggiornata dello stato emotivo, con normalizzazione personale e
    meccanismo di feedback. Vedi main.py per un'applicazione interattiva
    completa da riga di comando.
    """

    def __init__(self, model: NoemaModel = None, log_path: str = None,
                 params_path: str = None, reset_state_on_load: bool = True):
        self.model = model or NoemaModel()
        if params_path:
            self.model.load_params(params_path)
            if reset_state_on_load:
                self.model.reset_state()
        self.log_path = log_path
        self._last_record: dict = None

    def ingest_turn(self, text: str, keydown_times: list, backspace_count: int,
                     response_latency_s: float, is_followup: bool,
                     followup_depth: int, hour_of_day: int = None) -> dict:
        hour_of_day = hour_of_day if hour_of_day is not None else datetime.datetime.now().hour
        tf = text_features(text)
        kf = keystroke_features(keydown_times, backspace_count=backspace_count,
                                 personal_baseline=self.model.personal_typing_baseline())
        inf = interaction_features(response_latency_s, is_followup, followup_depth, hour_of_day)
        u = build_feature_vector(tf, kf, inf)
        state = self.model.step(u)
        conf = self.model.history[-1]["confidence"]
        nessuna_parola = all(tf.get(f"lex_{e}", 0.0) == 0.0 for e in EMOTIONS)

        v, a, d = state.pad
        record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "valence": float(v), "arousal": float(a), "dominance": float(d),
            "emozioni": {e: round(float(x), 3) for e, x in zip(EMOTIONS, state.intensities)},
            "emozioni_dominanti": state.dominanti(k=2),
            "confidence_proxy": conf,
            "label": genera_descrizione(state, conf, nessuna_parola_riconosciuta=nessuna_parola),
        }
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._last_record = record
        return record

    def provide_feedback(self, corretto: bool, emozione_corretta: str = None) -> None:
        """Inoltra il feedback umano sull'ultima stima al modello."""
        self.model.apply_feedback(corretto=corretto, emozione_corretta=emozione_corretta)

    def calibra_con_testo(self, testo_lungo: str, autore_e_soggetto_coincidono: bool = True) -> None:
        """
        Calibrazione opzionale con un testo scritto dalla STESSA persona
        che verra' monitorata (bio, articolo, post) — l'alternativa che
        rispetta il consenso alla raccolta di profili social/pubblici di
        terzi, che questo progetto NON implementa (vedi nota nella
        documentazione). Suddivide il testo in frasi e le processa come
        turni di calibrazione, senza dati di digitazione reali (usa stime
        neutre di default per quella parte).
        """
        if not autore_e_soggetto_coincidono:
            raise ValueError(
                "calibra_con_testo() va usato solo con testo scritto dalla stessa "
                "persona che verra' monitorata, con il suo consenso. Interrompo."
            )
        frasi = [f.strip() for f in re.split(r"[.!?\n]+", testo_lungo) if f.strip()]
        print(f"[NOEMA] Calibrazione con {len(frasi)} frasi fornite dall'utente...")
        for frase in frasi:
            tf = text_features(frase)
            kf = keystroke_features([0.15, 0.18, 0.16, 0.2])  # stima neutra, nessun dato reale
            inf = interaction_features(5.0, False, 0, 12)
            u = build_feature_vector(tf, kf, inf)
            self.model.step(u)
        print("[NOEMA] Calibrazione completata.")
