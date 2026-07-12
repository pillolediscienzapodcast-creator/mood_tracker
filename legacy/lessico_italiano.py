# -*- coding: utf-8 -*-
"""
Risorse linguistiche italiane per NOEMA.

Lessico emotivo espanso (circa 150 voci) organizzato sulle 8 emozioni di
base del modello di Plutchik, con supporto per negazione, intensificatori,
suffissi superlativi ed emoji/emoticon comuni.

ONESTA' METODOLOGICA: questo e' un lessico dimostrativo costruito a mano,
NON una risorsa validata psicometricamente su larga scala (a differenza,
ad esempio, di NRC-VAD o LIWC). Copre alcune centinaia di forme comuni,
non l'intero vocabolario emotivo italiano. Per un uso in produzione reale
andrebbe integrato con una risorsa linguistica validata e più ampia,
idealmente curata da un linguista computazionale.
"""

EMOTIONS = ["gioia", "fiducia", "paura", "sorpresa", "tristezza",
            "disgusto", "rabbia", "anticipazione"]

# parola (minuscolo, senza accenti problematici) -> {emozione: peso 0-1}
LESSICO = {
    # --- Gioia ---
    "felice": {"gioia": 0.8}, "felicissimo": {"gioia": 1.0}, "felicissima": {"gioia": 1.0},
    "contento": {"gioia": 0.6}, "contenta": {"gioia": 0.6}, "allegro": {"gioia": 0.7},
    "allegra": {"gioia": 0.7}, "gioioso": {"gioia": 0.8}, "entusiasta": {"gioia": 0.8, "anticipazione": 0.3},
    "entusiasmante": {"gioia": 0.6, "anticipazione": 0.3}, "divertente": {"gioia": 0.5},
    "soddisfatto": {"gioia": 0.5, "fiducia": 0.3}, "soddisfatta": {"gioia": 0.5, "fiducia": 0.3},
    "radioso": {"gioia": 0.8}, "splendido": {"gioia": 0.7}, "fantastico": {"gioia": 0.7},
    "magnifico": {"gioia": 0.7}, "bellissimo": {"gioia": 0.6}, "ottimo": {"gioia": 0.5},
    "perfetto": {"gioia": 0.5, "fiducia": 0.3}, "meraviglioso": {"gioia": 0.8, "sorpresa": 0.2},
    "gioia": {"gioia": 0.8}, "felicita": {"gioia": 0.8}, "ridere": {"gioia": 0.5},
    "sorridere": {"gioia": 0.4}, "orgoglioso": {"gioia": 0.5, "fiducia": 0.4},
    "orgogliosa": {"gioia": 0.5, "fiducia": 0.4}, "bello": {"gioia": 0.3},

    # --- Fiducia ---
    "fiducia": {"fiducia": 0.8}, "sicuro": {"fiducia": 0.6}, "sicura": {"fiducia": 0.6},
    "sicurezza": {"fiducia": 0.6}, "tranquillo": {"fiducia": 0.5}, "tranquilla": {"fiducia": 0.5},
    "rilassato": {"fiducia": 0.5}, "rilassata": {"fiducia": 0.5}, "calmo": {"fiducia": 0.4},
    "calma": {"fiducia": 0.4}, "sereno": {"fiducia": 0.5, "gioia": 0.2}, "serena": {"fiducia": 0.5, "gioia": 0.2},
    "affidabile": {"fiducia": 0.6}, "onesto": {"fiducia": 0.5}, "leale": {"fiducia": 0.5},
    "credere": {"fiducia": 0.4}, "fidarsi": {"fiducia": 0.5}, "ottimista": {"fiducia": 0.5, "anticipazione": 0.3},
    "speranzoso": {"fiducia": 0.4, "anticipazione": 0.5}, "grazie": {"fiducia": 0.4, "gioia": 0.2},
    "apprezzo": {"fiducia": 0.4, "gioia": 0.2}, "stimare": {"fiducia": 0.4},

    # --- Paura ---
    "paura": {"paura": 0.8}, "spaventato": {"paura": 0.8}, "spaventata": {"paura": 0.8},
    "terrorizzato": {"paura": 1.0}, "terrorizzata": {"paura": 1.0}, "ansioso": {"paura": 0.6},
    "ansiosa": {"paura": 0.6}, "ansia": {"paura": 0.6}, "preoccupato": {"paura": 0.5, "tristezza": 0.2},
    "preoccupata": {"paura": 0.5, "tristezza": 0.2}, "preoccupazione": {"paura": 0.5},
    "nervoso": {"paura": 0.5, "rabbia": 0.2}, "nervosa": {"paura": 0.5, "rabbia": 0.2},
    "timore": {"paura": 0.5}, "timoroso": {"paura": 0.5}, "spavento": {"paura": 0.6},
    "panico": {"paura": 0.9}, "insicuro": {"paura": 0.4}, "insicura": {"paura": 0.4},
    "incerto": {"paura": 0.3}, "incerta": {"paura": 0.3}, "tremare": {"paura": 0.5},
    "agitato": {"paura": 0.4, "rabbia": 0.2}, "agitata": {"paura": 0.4, "rabbia": 0.2},

    # --- Sorpresa ---
    "sorpreso": {"sorpresa": 0.7}, "sorpresa": {"sorpresa": 0.7}, "stupito": {"sorpresa": 0.7},
    "stupita": {"sorpresa": 0.7}, "stupore": {"sorpresa": 0.7}, "incredibile": {"sorpresa": 0.6, "gioia": 0.2},
    "inaspettato": {"sorpresa": 0.6}, "inaspettata": {"sorpresa": 0.6}, "wow": {"sorpresa": 0.7, "gioia": 0.2},
    "scioccato": {"sorpresa": 0.7, "paura": 0.2}, "scioccata": {"sorpresa": 0.7, "paura": 0.2},
    "shock": {"sorpresa": 0.7, "paura": 0.3}, "imprevisto": {"sorpresa": 0.5}, "meraviglia": {"sorpresa": 0.5, "gioia": 0.3},

    # --- Tristezza ---
    "triste": {"tristezza": 0.8}, "tristissimo": {"tristezza": 1.0}, "tristissima": {"tristezza": 1.0},
    "deluso": {"tristezza": 0.6}, "delusa": {"tristezza": 0.6}, "delusione": {"tristezza": 0.6},
    "infelice": {"tristezza": 0.7}, "depresso": {"tristezza": 0.8}, "depressa": {"tristezza": 0.8},
    "giu": {"tristezza": 0.5}, "abbattuto": {"tristezza": 0.7}, "abbattuta": {"tristezza": 0.7},
    "tristezza": {"tristezza": 0.8},
    "malinconico": {"tristezza": 0.6}, "malinconica": {"tristezza": 0.6}, "solo": {"tristezza": 0.4},
    "sola": {"tristezza": 0.4}, "solitudine": {"tristezza": 0.6}, "sconfortato": {"tristezza": 0.7},
    "sconfortata": {"tristezza": 0.7}, "disperato": {"tristezza": 0.9, "paura": 0.3},
    "disperata": {"tristezza": 0.9, "paura": 0.3}, "disperazione": {"tristezza": 0.9},
    "piangere": {"tristezza": 0.6}, "lacrime": {"tristezza": 0.5}, "dispiaciuto": {"tristezza": 0.5},
    "dispiaciuta": {"tristezza": 0.5}, "rammarico": {"tristezza": 0.4}, "nostalgia": {"tristezza": 0.4},
    "stanco": {"tristezza": 0.3}, "stanca": {"tristezza": 0.3}, "stanchissimo": {"tristezza": 0.5},
    "stanchissima": {"tristezza": 0.5}, "esausto": {"tristezza": 0.5}, "esausta": {"tristezza": 0.5},
    "sfinito": {"tristezza": 0.5}, "sfinita": {"tristezza": 0.5}, "pesante": {"tristezza": 0.3},

    # --- Disgusto ---
    "disgusto": {"disgusto": 0.8}, "disgustato": {"disgusto": 0.8}, "disgustata": {"disgusto": 0.8},
    "schifo": {"disgusto": 0.7}, "ripugnante": {"disgusto": 0.8}, "orribile": {"disgusto": 0.6, "tristezza": 0.2},
    "nauseante": {"disgusto": 0.7}, "fastidio": {"disgusto": 0.4, "rabbia": 0.3},
    "irritante": {"disgusto": 0.4, "rabbia": 0.4}, "insopportabile": {"disgusto": 0.5, "rabbia": 0.4},
    "odioso": {"disgusto": 0.5, "rabbia": 0.3}, "ributtante": {"disgusto": 0.7},

    # --- Rabbia ---
    "arrabbiato": {"rabbia": 0.8}, "arrabbiata": {"rabbia": 0.8}, "arrabbiatissimo": {"rabbia": 1.0},
    "arrabbiatissima": {"rabbia": 1.0}, "rabbia": {"rabbia": 0.8}, "furioso": {"rabbia": 0.9},
    "furiosa": {"rabbia": 0.9}, "furia": {"rabbia": 0.8}, "incazzato": {"rabbia": 0.9},
    "incazzata": {"rabbia": 0.9}, "irritato": {"rabbia": 0.5}, "irritata": {"rabbia": 0.5},
    "infastidito": {"rabbia": 0.4}, "infastidita": {"rabbia": 0.4}, "indignato": {"rabbia": 0.6},
    "indignata": {"rabbia": 0.6}, "esasperato": {"rabbia": 0.6}, "esasperata": {"rabbia": 0.6},
    "odio": {"rabbia": 0.7, "disgusto": 0.3}, "odiare": {"rabbia": 0.7, "disgusto": 0.3},
    "inaccettabile": {"rabbia": 0.5}, "ingiusto": {"rabbia": 0.4, "tristezza": 0.2},
    "frustrato": {"rabbia": 0.5, "tristezza": 0.2}, "frustrata": {"rabbia": 0.5, "tristezza": 0.2},
    "frustrazione": {"rabbia": 0.5}, "rotto": {"rabbia": 0.3}, "urgente": {"paura": 0.3, "rabbia": 0.2},

    # --- Anticipazione ---
    "aspettare": {"anticipazione": 0.4}, "attesa": {"anticipazione": 0.4}, "curioso": {"anticipazione": 0.5},
    "curiosa": {"anticipazione": 0.5}, "curiosita": {"anticipazione": 0.5}, "speranza": {"anticipazione": 0.5, "fiducia": 0.3},
    "sperare": {"anticipazione": 0.4, "fiducia": 0.2}, "desiderio": {"anticipazione": 0.4},
    "desiderare": {"anticipazione": 0.4}, "prevedere": {"anticipazione": 0.3}, "progetto": {"anticipazione": 0.3},
    "futuro": {"anticipazione": 0.3}, "presto": {"anticipazione": 0.3}, "prossimo": {"anticipazione": 0.2},

    # --- Urgenza / neutro operativo (residuo dal lessico precedente) ---
    "problema": {"tristezza": 0.2, "rabbia": 0.2}, "aiuto": {"paura": 0.2, "anticipazione": 0.2},
    "bene": {"gioia": 0.3, "fiducia": 0.2}, "male": {"tristezza": 0.3, "disgusto": 0.1},

    # --- Espansione: vocabolario emotivo comune della vita quotidiana,
    # mancante nella prima versione del lessico (parole come "emozionato"
    # non erano riconosciute, facendo risultare "neutro" anche messaggi
    # chiaramente emotivi — problema segnalato durante l'uso reale) ---
    "emozionato": {"gioia": 0.6, "sorpresa": 0.3}, "emozionata": {"gioia": 0.6, "sorpresa": 0.3},
    "eccitato": {"gioia": 0.6, "anticipazione": 0.4}, "eccitata": {"gioia": 0.6, "anticipazione": 0.4},
    "commosso": {"gioia": 0.5, "tristezza": 0.3}, "commossa": {"gioia": 0.5, "tristezza": 0.3},
    "euforico": {"gioia": 0.9}, "euforica": {"gioia": 0.9},
    "appagato": {"gioia": 0.5, "fiducia": 0.4}, "appagata": {"gioia": 0.5, "fiducia": 0.4},
    "raggiante": {"gioia": 0.8}, "spensierato": {"gioia": 0.5}, "spensierata": {"gioia": 0.5},

    "motivato": {"fiducia": 0.5, "anticipazione": 0.4}, "motivata": {"fiducia": 0.5, "anticipazione": 0.4},
    "ispirato": {"fiducia": 0.4, "anticipazione": 0.4}, "ispirata": {"fiducia": 0.4, "anticipazione": 0.4},
    "grato": {"fiducia": 0.5, "gioia": 0.3}, "grata": {"fiducia": 0.5, "gioia": 0.3},
    "riconoscente": {"fiducia": 0.5, "gioia": 0.3},
    "sollevato": {"fiducia": 0.5, "gioia": 0.3}, "sollevata": {"fiducia": 0.5, "gioia": 0.3},
    "sollievo": {"fiducia": 0.5, "gioia": 0.2},

    "allarmato": {"paura": 0.6}, "allarmata": {"paura": 0.6},
    "intimorito": {"paura": 0.5}, "intimorita": {"paura": 0.5},
    "angosciato": {"paura": 0.7, "tristezza": 0.2}, "angosciata": {"paura": 0.7, "tristezza": 0.2},
    "angoscia": {"paura": 0.7, "tristezza": 0.2}, "spaventoso": {"paura": 0.5}, "spaventosa": {"paura": 0.5},

    "sbalordito": {"sorpresa": 0.7}, "sbalordita": {"sorpresa": 0.7},
    "sbigottito": {"sorpresa": 0.6}, "sbigottita": {"sorpresa": 0.6},
    "spiazzato": {"sorpresa": 0.6}, "spiazzata": {"sorpresa": 0.6},

    "demoralizzato": {"tristezza": 0.7}, "demoralizzata": {"tristezza": 0.7},
    "scoraggiato": {"tristezza": 0.6}, "scoraggiata": {"tristezza": 0.6},
    "distrutto": {"tristezza": 0.7}, "distrutta": {"tristezza": 0.7},
    "affranto": {"tristezza": 0.8}, "affranta": {"tristezza": 0.8},
    "desolato": {"tristezza": 0.6}, "desolata": {"tristezza": 0.6},
    "spento": {"tristezza": 0.4}, "spenta": {"tristezza": 0.4},
    "vuoto": {"tristezza": 0.5}, "vuota": {"tristezza": 0.5},
    "incompreso": {"tristezza": 0.5}, "incompresa": {"tristezza": 0.5},
    "abbandonato": {"tristezza": 0.6}, "abbandonata": {"tristezza": 0.6},
    "rifiutato": {"tristezza": 0.6}, "rifiutata": {"tristezza": 0.6},
    "nostalgico": {"tristezza": 0.4}, "nostalgica": {"tristezza": 0.4},

    "schifato": {"disgusto": 0.7}, "schifata": {"disgusto": 0.7},
    "rivoltante": {"disgusto": 0.7}, "stomachevole": {"disgusto": 0.7},
    "raccapricciante": {"disgusto": 0.8},

    "imbestialito": {"rabbia": 0.9}, "imbestialita": {"rabbia": 0.9},
    "spazientito": {"rabbia": 0.5}, "spazientita": {"rabbia": 0.5},
    "stufo": {"rabbia": 0.5, "disgusto": 0.2}, "stufa": {"rabbia": 0.5, "disgusto": 0.2},
    "seccato": {"rabbia": 0.4}, "seccata": {"rabbia": 0.4},
    "scocciato": {"rabbia": 0.4}, "scocciata": {"rabbia": 0.4},

    "anticipazione": {"anticipazione": 0.7},
    "impaziente": {"anticipazione": 0.6, "rabbia": 0.2},
    "trepidante": {"anticipazione": 0.6},

    "geloso": {"rabbia": 0.4, "tristezza": 0.3}, "gelosa": {"rabbia": 0.4, "tristezza": 0.3},
    "gelosia": {"rabbia": 0.4, "tristezza": 0.3},
    "invidioso": {"rabbia": 0.3, "disgusto": 0.3}, "invidiosa": {"rabbia": 0.3, "disgusto": 0.3},
    "invidia": {"rabbia": 0.3, "disgusto": 0.3},
    "colpevole": {"tristezza": 0.4, "paura": 0.2}, "colpa": {"tristezza": 0.4, "paura": 0.2},
    "imbarazzato": {"paura": 0.3, "tristezza": 0.2}, "imbarazzata": {"paura": 0.3, "tristezza": 0.2},
    "imbarazzo": {"paura": 0.3, "tristezza": 0.2},
    "confuso": {"sorpresa": 0.3, "paura": 0.2}, "confusa": {"sorpresa": 0.3, "paura": 0.2},
    "frastornato": {"sorpresa": 0.4, "paura": 0.2}, "frastornata": {"sorpresa": 0.4, "paura": 0.2},
    "sopraffatto": {"paura": 0.4, "tristezza": 0.3}, "sopraffatta": {"paura": 0.4, "tristezza": 0.3},
    "indifferente": {"tristezza": 0.2, "disgusto": 0.1},
    "annoiato": {"tristezza": 0.2, "disgusto": 0.2}, "annoiata": {"tristezza": 0.2, "disgusto": 0.2},

    # --- Gergo, slang e linguaggio colloquiale da messaggistica ---
    # Necessario per un uso realistico: nel testo informale reale le
    # persone esprimono le emozioni forti anche con esclamazioni gergali
    # e parolacce comuni, non solo con l'italiano formale. Sono incluse
    # solo espressioni volgari generiche di uso corrente (esclamazioni,
    # intensificatori emotivi) — MAI termini offensivi rivolti a persone,
    # gruppi o identita' specifiche.

    # Gioia (gergo)
    "figo": {"gioia": 0.6}, "fico": {"gioia": 0.6}, "figata": {"gioia": 0.6}, "top": {"gioia": 0.6},
    "spacca": {"gioia": 0.6}, "sballo": {"gioia": 0.7},
    "pazzesco": {"gioia": 0.5, "sorpresa": 0.4}, "pazzesca": {"gioia": 0.5, "sorpresa": 0.4},
    "gasato": {"gioia": 0.6, "anticipazione": 0.3}, "gasata": {"gioia": 0.6, "anticipazione": 0.3},
    "arzillo": {"gioia": 0.5}, "arzilla": {"gioia": 0.5},
    "favoloso": {"gioia": 0.7}, "favolosa": {"gioia": 0.7},
    "evviva": {"gioia": 0.7}, "urra": {"gioia": 0.6},
    "spassoso": {"gioia": 0.5}, "spassosa": {"gioia": 0.5},
    "esilarante": {"gioia": 0.6},
    "adoro": {"gioia": 0.6, "fiducia": 0.3}, "adorare": {"gioia": 0.6, "fiducia": 0.3},
    "stracontento": {"gioia": 0.8}, "stracontenta": {"gioia": 0.8},
    "ahah": {"gioia": 0.4}, "ahaha": {"gioia": 0.4}, "ahahah": {"gioia": 0.5},
    "haha": {"gioia": 0.4}, "hihi": {"gioia": 0.3}, "lol": {"gioia": 0.3},

    # Fiducia (gergo)
    "tranqui": {"fiducia": 0.5}, "apposto": {"fiducia": 0.4},

    # Paura (gergo)
    "fifa": {"paura": 0.6}, "strizza": {"paura": 0.5}, "brividi": {"paura": 0.4, "sorpresa": 0.2},
    "terrore": {"paura": 0.8},

    # Sorpresa / esclamazioni miste (molte esclamazioni gergali italiane
    # oscillano fra sorpresa e rabbia a seconda del contesto: pesi su
    # entrambe, non un'unica categoria netta)
    "cavolo": {"sorpresa": 0.3, "rabbia": 0.2}, "cacchio": {"sorpresa": 0.3, "rabbia": 0.2},
    "caspita": {"sorpresa": 0.4}, "accidenti": {"sorpresa": 0.3, "rabbia": 0.3},
    "minchia": {"sorpresa": 0.4, "rabbia": 0.3}, "cazzo": {"rabbia": 0.5, "sorpresa": 0.3},
    "madonna": {"sorpresa": 0.4}, "boh": {"sorpresa": 0.15}, "miseria": {"rabbia": 0.3},

    # Tristezza (gergo)
    "depre": {"tristezza": 0.6}, "moscio": {"tristezza": 0.4}, "moscia": {"tristezza": 0.4},
    "sfatto": {"tristezza": 0.4, "paura": 0.2}, "sfatta": {"tristezza": 0.4, "paura": 0.2},

    # Disgusto (gergo)
    "schifezza": {"disgusto": 0.6}, "immondo": {"disgusto": 0.6}, "immonda": {"disgusto": 0.6},
    "vomitevole": {"disgusto": 0.7}, "vomito": {"disgusto": 0.5},
    "cagata": {"disgusto": 0.5, "rabbia": 0.3}, "stronzata": {"disgusto": 0.4, "rabbia": 0.4},
    "cringe": {"disgusto": 0.4, "paura": 0.2},

    # Rabbia (gergo — la categoria con piu' varianti volgari nell'uso reale)
    "vaffanculo": {"rabbia": 0.8}, "merda": {"rabbia": 0.4, "disgusto": 0.4},
    "maledizione": {"rabbia": 0.5}, "maledetto": {"rabbia": 0.4}, "maledetta": {"rabbia": 0.4},
    "dannazione": {"rabbia": 0.4}, "sbroccare": {"rabbia": 0.6},
    "imbufalito": {"rabbia": 0.8}, "imbufalita": {"rabbia": 0.8},
    "sclerare": {"rabbia": 0.4, "paura": 0.2}, "sclerato": {"rabbia": 0.4, "paura": 0.2},
    "sclerata": {"rabbia": 0.4, "paura": 0.2}, "sclero": {"rabbia": 0.3, "paura": 0.3},
    "tilt": {"paura": 0.3, "rabbia": 0.3},

    # Anticipazione (gergo)
    "scalpitare": {"anticipazione": 0.5}, "fremere": {"anticipazione": 0.5},
    "hype": {"anticipazione": 0.6, "gioia": 0.3},
    "carico": {"anticipazione": 0.5, "gioia": 0.3}, "carica": {"anticipazione": 0.5, "gioia": 0.3},
}

# --- Vocabolario italiano comune (non gergale), mancante nelle sezioni
# precedenti: verbi, sostantivi e aggettivi di uso quotidiano — necessario
# perche' anche messaggi semplici e non gergali ("mi piace", "che dolore",
# "sono stressato") trovino corrispondenza nel lessico. ---
LESSICO_COMUNE = {
    # Gioia
    "piacere": {"gioia": 0.4}, "piace": {"gioia": 0.4}, "amore": {"gioia": 0.5, "fiducia": 0.3},
    "amo": {"gioia": 0.6, "fiducia": 0.3}, "amabile": {"gioia": 0.4},
    "simpatico": {"gioia": 0.4}, "simpatica": {"gioia": 0.4},
    "divertimento": {"gioia": 0.5}, "buono": {"gioia": 0.3}, "buona": {"gioia": 0.3},
    "buonissimo": {"gioia": 0.6}, "buonissima": {"gioia": 0.6}, "ok": {"gioia": 0.2, "fiducia": 0.3},
    "delizia": {"gioia": 0.5}, "delizioso": {"gioia": 0.5}, "deliziosa": {"gioia": 0.5},
    "piacevole": {"gioia": 0.4}, "benessere": {"gioia": 0.4, "fiducia": 0.3},
    "soddisfazione": {"gioia": 0.4, "fiducia": 0.3}, "vittoria": {"gioia": 0.6},
    "successo": {"gioia": 0.6}, "esaltante": {"gioia": 0.6}, "rilassante": {"gioia": 0.3, "fiducia": 0.3},
    "meglio": {"gioia": 0.3, "fiducia": 0.2}, "spaccare": {"gioia": 0.6}, "asso": {"gioia": 0.5},
    "bomba": {"gioia": 0.5}, "guarito": {"gioia": 0.4, "fiducia": 0.3}, "guarita": {"gioia": 0.4, "fiducia": 0.3},

    # Fiducia
    "certezza": {"fiducia": 0.5}, "certo": {"fiducia": 0.3}, "certa": {"fiducia": 0.3},
    "sicurissimo": {"fiducia": 0.7}, "sicurissima": {"fiducia": 0.7}, "fede": {"fiducia": 0.4},
    "rassicurante": {"fiducia": 0.5}, "conforto": {"fiducia": 0.4}, "confortante": {"fiducia": 0.4},
    "pace": {"fiducia": 0.5}, "quieto": {"fiducia": 0.4}, "quieta": {"fiducia": 0.4},
    "positivo": {"fiducia": 0.4}, "positiva": {"fiducia": 0.4}, "prego": {"fiducia": 0.2, "gioia": 0.2},
    "perdono": {"fiducia": 0.3},

    # Paura
    "temere": {"paura": 0.5}, "timido": {"paura": 0.3}, "timida": {"paura": 0.3},
    "pauroso": {"paura": 0.5}, "paurosa": {"paura": 0.5}, "stress": {"paura": 0.4, "rabbia": 0.2},
    "stressato": {"paura": 0.4, "rabbia": 0.3}, "stressata": {"paura": 0.4, "rabbia": 0.3},
    "turbato": {"paura": 0.4, "tristezza": 0.3}, "turbata": {"paura": 0.4, "tristezza": 0.3},
    "scosso": {"paura": 0.4}, "scossa": {"paura": 0.4}, "allerta": {"paura": 0.4},
    "allarme": {"paura": 0.5}, "pericolo": {"paura": 0.5}, "rischio": {"paura": 0.3},
    "minaccia": {"paura": 0.5}, "minacciare": {"paura": 0.5}, "vulnerabile": {"paura": 0.4},
    "indifeso": {"paura": 0.4}, "indifesa": {"paura": 0.4}, "rabbrividire": {"paura": 0.5},

    # Sorpresa
    "strabiliante": {"sorpresa": 0.6}, "sbalorditivo": {"sorpresa": 0.6}, "sbalorditiva": {"sorpresa": 0.6},
    "clamoroso": {"sorpresa": 0.5}, "clamorosa": {"sorpresa": 0.5}, "eclatante": {"sorpresa": 0.5},
    "inatteso": {"sorpresa": 0.5}, "inattesa": {"sorpresa": 0.5},

    # Tristezza
    "dolore": {"tristezza": 0.5}, "doloroso": {"tristezza": 0.5}, "dolorosa": {"tristezza": 0.5},
    "soffrire": {"tristezza": 0.6}, "sofferenza": {"tristezza": 0.6},
    "addolorato": {"tristezza": 0.6}, "addolorata": {"tristezza": 0.6}, "mestizia": {"tristezza": 0.5},
    "sconsolato": {"tristezza": 0.6}, "sconsolata": {"tristezza": 0.6}, "cupo": {"tristezza": 0.4},
    "cupa": {"tristezza": 0.4}, "fallimento": {"tristezza": 0.5}, "sconfitta": {"tristezza": 0.5},
    "perdita": {"tristezza": 0.5}, "perdere": {"tristezza": 0.3}, "lutto": {"tristezza": 0.7},
    "buio": {"tristezza": 0.3}, "peggio": {"tristezza": 0.3, "rabbia": 0.2},
    "ahi": {"tristezza": 0.2, "paura": 0.2}, "ahia": {"tristezza": 0.2, "paura": 0.2},

    # Disgusto
    "repellente": {"disgusto": 0.7}, "orrendo": {"disgusto": 0.6}, "orrenda": {"disgusto": 0.6},
    "orripilante": {"disgusto": 0.7}, "disprezzo": {"disgusto": 0.5, "rabbia": 0.3},
    "disprezzare": {"disgusto": 0.5, "rabbia": 0.3}, "sdegno": {"disgusto": 0.3, "rabbia": 0.4},
    "sdegnato": {"disgusto": 0.3, "rabbia": 0.4}, "sdegnata": {"disgusto": 0.3, "rabbia": 0.4},

    # Rabbia
    "litigare": {"rabbia": 0.5}, "litigio": {"rabbia": 0.5}, "conflitto": {"rabbia": 0.4},
    "collera": {"rabbia": 0.7}, "ira": {"rabbia": 0.7}, "irato": {"rabbia": 0.6}, "irata": {"rabbia": 0.6},
    "ostilita": {"rabbia": 0.5}, "ostile": {"rabbia": 0.5}, "aggressivo": {"rabbia": 0.5},
    "aggressiva": {"rabbia": 0.5}, "aggressivita": {"rabbia": 0.5}, "esplodere": {"rabbia": 0.5},
    "esplosivo": {"rabbia": 0.4}, "uffa": {"rabbia": 0.3}, "mannaggia": {"rabbia": 0.3},
    "rottura": {"rabbia": 0.4}, "sbagliato": {"rabbia": 0.2, "tristezza": 0.2},

    # Anticipazione
    "attendere": {"anticipazione": 0.4}, "aspettativa": {"anticipazione": 0.4},
    "aspettative": {"anticipazione": 0.4}, "previsione": {"anticipazione": 0.3},
    "imminente": {"anticipazione": 0.4}, "prossimamente": {"anticipazione": 0.4},
    "forza": {"anticipazione": 0.4, "gioia": 0.3},

    # Mista / neutro-operativo
    "giusto": {"fiducia": 0.2},
}
LESSICO.update(LESSICO_COMUNE)

# Parole tipicamente soggette a censura volontaria nella scrittura reale
# (ca**o, m***a...). Usato per disambiguare il matching jolly quando piu'
# di una parola del lessico condivide la stessa lunghezza e lo stesso
# schema di lettere non censurate: chi scrive "ca**o" sta quasi
# certamente censurando "cazzo", non una parola neutra come "calmo" che
# nessuno ha motivo di censurare.
PAROLE_CENSURABILI = {
    "cazzo", "minchia", "vaffanculo", "merda", "stronzata", "cagata",
    "puttana", "troia", "coglione", "coglioni", "bastardo", "bastarda",
}

# Frasi idiomatiche comuni (2-4 parole), riconosciute come unita' PRIMA
# della scomposizione a singola parola. Necessario perche' molte
# espressioni italiane hanno un significato che non deriva dalla somma
# delle parole singole — l'esempio piu' chiaro e' "non vedo l'ora", che
# contiene "non" ma non e' affatto una negazione: e' attesa positiva.
# Le chiavi sono tuple di token in minuscolo, nello stesso formato in cui
# la tokenizzazione di text_features() li produce.
FRASI = {
    ("non", "vedo", "l'ora"): {"anticipazione": 0.7, "gioia": 0.2},
    ("non", "vedo", "lora"): {"anticipazione": 0.7, "gioia": 0.2},
    ("che", "due", "palle"): {"rabbia": 0.6},
    ("che", "palle"): {"rabbia": 0.5},
    ("che", "due", "maroni"): {"rabbia": 0.6},
    ("in", "bocca", "al", "lupo"): {"fiducia": 0.4, "anticipazione": 0.3},
    ("sono", "a", "pezzi"): {"tristezza": 0.6},
    ("sei", "a", "pezzi"): {"tristezza": 0.6},
    ("mi", "sento", "a", "pezzi"): {"tristezza": 0.6},
    ("giu", "di", "morale"): {"tristezza": 0.5},
    ("giù", "di", "morale"): {"tristezza": 0.5},
    ("su", "di", "giri"): {"gioia": 0.5, "anticipazione": 0.3},
    ("voglia", "matta"): {"anticipazione": 0.5, "gioia": 0.3},
    ("non", "ne", "posso", "piu"): {"rabbia": 0.5, "tristezza": 0.2},
    ("non", "ne", "posso", "più"): {"rabbia": 0.5, "tristezza": 0.2},
    ("stufo", "marcio"): {"rabbia": 0.6},
    ("stufa", "marcia"): {"rabbia": 0.6},
    ("meno", "male"): {"fiducia": 0.4, "gioia": 0.3},
    ("grazie", "al", "cielo"): {"fiducia": 0.4, "gioia": 0.3},
    ("rottura", "di", "scatole"): {"rabbia": 0.5},
}

# Negatori: se compaiono in una piccola finestra di parole prima di una
# parola emotiva, ne attenuano/invertono il contributo (non un'inversione
# speculare: "non sono felice" non equivale a "sono triste", e' piu'
# vicino a uno stato smorzato/ambiguo).
NEGATORI = {"non", "mai", "nessuno", "nessuna", "niente", "nulla", "senza", "no",
            "neanche", "nemmeno", "manco", "mica", "nn"}

# Intensificatori e diminutori
INTENSIFICATORI = {"molto", "davvero", "tantissimo", "estremamente", "incredibilmente",
                    "cosi", "tanto", "troppo", "super", "assolutamente", "veramente",
                    "mega", "iper", "parecchio", "assai", "bestiale", "esageratamente"}
DIMINUTORI = {"poco", "leggermente", "abbastanza", "quasi", "appena"}

# Emoji/emoticon comuni -> emozione associata (ricerca per substring, non
# per token separato, dato che spesso sono attaccate al testo)
EMOJI = {
    "😊": {"gioia": 0.6}, "🙂": {"gioia": 0.4}, "😄": {"gioia": 0.8}, "😃": {"gioia": 0.7},
    "😁": {"gioia": 0.7}, "❤️": {"gioia": 0.5, "fiducia": 0.3}, "👍": {"fiducia": 0.4, "gioia": 0.3},
    "😢": {"tristezza": 0.7}, "😭": {"tristezza": 0.9}, "☹️": {"tristezza": 0.5},
    "😡": {"rabbia": 0.9}, "😠": {"rabbia": 0.7}, "🤬": {"rabbia": 1.0},
    "😱": {"paura": 0.8}, "😨": {"paura": 0.7}, "😰": {"paura": 0.7},
    "😲": {"sorpresa": 0.7}, "😮": {"sorpresa": 0.5}, "🙄": {"disgusto": 0.4},
    "🤢": {"disgusto": 0.8}, ":)": {"gioia": 0.5}, ":(": {"tristezza": 0.5},
    ":d": {"gioia": 0.7}, ":'(": {"tristezza": 0.7}, ";)": {"gioia": 0.3},
}

# Pronomi per la feature di auto-focus. NOTA INTERPRETATIVA: un rapporto
# piu' alto di pronomi in prima persona singolare e' un correlato
# linguistico discusso in letteratura psicolinguistica (es. Pennebaker),
# ma da solo NON e' prova di un particolare stato emotivo — e' un segnale
# debole tra tanti, va trattato come tale.
PRONOMI_SE = {"io", "mi", "me", "mio", "mia", "miei", "mie"}
PRONOMI_ALTRI = {"noi", "ci", "nostro", "nostra", "nostri", "nostre", "loro", "voi"}

# Coordinate approssimative (Valenza, Arousal, Dominanza) per ciascuna
# emozione di base, secondo posizionamenti standard usati in letteratura
# di affective computing (circumplex di Russell, ruota di Plutchik).
# Valori illustrativi/approssimativi, non costanti psicometriche precise.
PAD_COORDS = {
    "gioia":         (0.80,  0.50,  0.40),
    "fiducia":       (0.60, -0.20,  0.30),
    "paura":         (-0.60, 0.70, -0.60),
    "sorpresa":      (0.10,  0.80, -0.10),
    "tristezza":     (-0.70, -0.50, -0.50),
    "disgusto":      (-0.70, 0.20,  0.10),
    "rabbia":        (-0.60, 0.80,  0.50),
    "anticipazione": (0.30,  0.40,  0.20),
}
