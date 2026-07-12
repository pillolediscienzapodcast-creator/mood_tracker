# NOEMA — Mood Tracker

Applicazione full-stack per il **tracciamento emotivo adattivo** a partire dal
testo e dai segnali comportamentali di digitazione. Il cuore del progetto è
**NOEMA**, un motore di inferenza emotiva *online* e *personalizzato*: apprende
in modo incrementale, turno dopo turno, il modo di esprimersi di una singola
persona e ne stima lo stato emotivo lungo le 8 emozioni di base di Plutchik più
un riassunto dimensionale PAD (Valenza / Arousal / Dominanza).

> ⚠️ **Disclaimer.** È un **prototipo di ricerca**, non uno strumento
> diagnostico. Le stime sono inferenze automatiche da *proxy comportamentali*
> (contenuto testuale, ritmo di digitazione, latenze), non letture certe dello
> stato reale di una persona. Non va usato per decisioni cliniche o valutazioni
> sulle persone.

---

## 1. Scopo

L'obiettivo è dimostrare un'architettura in cui la stima emotiva:

- **si personalizza** su chi scrive, invece di applicare un classificatore
  statico uguale per tutti;
- **apprende online**, aggiornando i propri parametri a ogni turno senza
  ri-addestramenti offline;
- **è interpretabile e onesta**: restituisce sempre una misura di *confidenza*,
  segnala quando nessuna parola è stata riconosciuta e accompagna ogni stima con
  una descrizione testuale in italiano e con un disclaimer esplicito;
- **rispetta la privacy**: per default non memorizza il testo grezzo dei
  messaggi, ma solo le feature numeriche e gli esiti.

Il tracciamento migliora nel tempo grazie al **feedback umano esplicito**
(conferma/correzione della stima), che viene consolidato periodicamente nei
parametri del modello.

---

## 2. Principio di funzionamento dell'algoritmo

NOEMA è un **modello a spazio di stato non lineare** con apprendimento online,
ispirato al *predictive coding*. A ogni turno percorre la pipeline seguente.

### 2.1 Dal testo alle feature (vettore `u`, 24 dimensioni)

Ogni turno viene tradotto in un vettore di input `u` di **24 feature**
(`app/engine/features.py`), nell'ordine canonico definito da `FEATURE_ORDER`:

| Blocco | N. | Contenuto |
| ------ | -- | --------- |
| **Lessicali** | 8 | un punteggio per emozione, dal lessico italiano |
| **Stilistiche** | 7 | lunghezza frase, tasso di `!`, `?`, `...`, MAIUSCOLE, auto-focus (pronomi), caratteri ripetuti |
| **Digitazione** | 5 | velocità, variabilità del ritmo, *burstiness*, tasso di errore (backspace), velocità **relativa** al proprio baseline |
| **Interazione** | 4 | latenza di risposta, *follow-up*, profondità del follow-up, fase circadiana (`sin` dell'ora del giorno) |

L'analisi lessicale (`app/engine/matching.py` + `lexicon/lessico_it.json`, ~488
voci costruite a mano) gestisce:

- **frasi idiomatiche** riconosciute come unità prima delle singole parole
  (es. *"non vedo l'ora"* → anticipazione, non negazione);
- **negazione** (finestra all'indietro), **intensificatori/diminutori**
  (finestra bidirezionale), **suffissi superlativi** (`-issimo`);
- **scrittura non standard**: lettere ripetute (`grazieee`), *leet* (`c4zzo`),
  `k`→`c`, censure con asterischi (`ca**o`), e come ultimo tentativo lo
  **stemming** morfologico italiano (Snowball via NLTK);
- **emoji/emoticon**.

Il vettore finale è **centrato, scalato e clippato** (difesa da NaN/inf e input
anomali) per riportare ogni feature su ordini di grandezza confrontabili.

### 2.2 La dinamica dello stato (`app/engine/model.py`)

Lo stato emotivo grezzo `z ∈ ℝ⁸` evolve secondo uno schema di
**Eulero-Maruyama**:

```
z_{t+1} = z_t + dt · [ −K (z_t − z0) + B · u_t ]
```

- `K` — richiamo verso il **baseline personale** `z0` (inerzia emotiva);
- `z0` — baseline appreso della persona;
- `B` — mappa **feature → emozioni**.

L'intensità *osservabile* di ciascuna emozione è `sigmoid(alpha · z)` in (0,1),
dove 0.5 = neutro/assente. **PAD** (Valenza, Arousal, Dominanza) è derivato a
valle come combinazione pesata dello *scostamento dal neutro* delle intensità.

### 2.3 L'apprendimento online (predictive coding)

Il modello *predice* le proprie feature e impara dall'errore di predizione:

```
u_pred = C · sigmoid(alpha · z_{t+1})      errore = u − u_pred
```

- **`C`** (mappa generativa) è stimata con **Recursive Least Squares (RLS)**,
  con fattore di dimenticanza `rls_lambda`;
- **`B`** è aggiornata per **discesa a gradiente** a tasso decrescente
  (`eta_B0 / (1 + t/tau_B)`) con *leakage* differenziato verso un prior: le
  connessioni non deliberate rilassano molto più fortemente verso zero;
- **`K`**, **`z0`** e **`alpha`** si **auto-regolano**: `K` insegue la
  volatilità dello stato, `z0` deriva lentamente verso lo stato osservato
  mantenendo gli assi bilanciati, `alpha` si adatta per mantenere una varianza
  target delle intensità recenti.

La **confidenza** (0–1) combina l'errore di predizione istantaneo e
l'incertezza residua sui parametri (traccia della covarianza RLS `P`).

> In uso *live* l'apprendimento auto-supervisionato è volutamente attenuato
> (`LIVE_LEARN_RATE = 0.15`): il testo reale fuori distribuzione potrebbe
> generare correzioni sproporzionate. La personalizzazione affidabile è delegata
> al feedback umano.

### 2.4 Feedback e consolidamento (`app/engine/feedback.py`)

Dopo ogni stima l'utente può **confermare** o **correggere**:

- la correzione sposta subito lo stato corrente verso il target dell'emozione
  indicata (aggiornamento bayesiano, non un reset);
- i feedback si accumulano e, ogni `consolidation_every` (default 5), vengono
  **consolidati** rielaborando `B` e `C` con i target *forniti dall'umano* e con
  peso maggiore di un passo online ordinario.

### 2.5 Pre-training e sanity check

I nuovi profili partono, se disponibile, da parametri **pre-allenati** offline
(`app/engine/pretrained/noema_params.json`), altrimenti da un modello "vergine"
col solo prior psicologico. Il pre-training genera turni sintetici sulle 8
emozioni, allena in modalità batch ed esegue una **batteria di correttezza
semantica** (`app/engine/sanity.py`): l'asset viene salvato **solo** se il
punteggio resta sopra la soglia di sicurezza (75%). Meglio nessun asset che uno
con associazioni sbagliate.

---

## 3. Stack tecnologico

| Livello | Tecnologie |
| ------- | ---------- |
| **Motore** | Python puro + **NumPy** (algebra lineare), **NLTK** (stemming Snowball italiano) |
| **Backend** | **FastAPI** · **SQLAlchemy 2** · **Alembic** · **Pydantic v2** / pydantic-settings · **PostgreSQL** (JSONB) · gestione dipendenze con [uv](https://docs.astral.sh/uv/) |
| **Frontend** | **Vue 3** · **TypeScript** · **Vite** · **Pinia** · **Vue Router** |
| **Infrastruttura** | **Docker Compose** v2 · **GitHub Actions** (CI) |
| **Qualità** | **Ruff** (lint + format) · **pytest** |

### Versioni ufficiali

| Componente | Versione |
| ---------- | -------- |
| Python     | 3.14     |
| Node.js    | 22 LTS   |
| PostgreSQL | 16       |
| Docker Compose | v2   |

---

## 4. Prerequisiti di installazione

**Percorso consigliato (Docker) — richiede solo:**

- [Docker](https://www.docker.com/) con **Docker Compose v2**

**Percorso sviluppo locale (senza Docker) — richiede:**

- [uv](https://docs.astral.sh/uv/) (installa e gestisce anche Python 3.14)
- [Node.js 22 LTS](https://nodejs.org/) con npm
- Un'istanza **PostgreSQL 16** raggiungibile secondo i valori in `backend/.env`

> NLTK usa lo stemmer Snowball, che è puramente algoritmico: **non serve
> scaricare corpora**. Se NLTK non è disponibile, il matching lessicale funziona
> comunque (senza il fallback di stemming).

---

## 5. Avvio rapido (Docker)

Due comandi, in questa sequenza:

```bash
cp backend/.env.example backend/.env     # 1. crea la configurazione (non versionata)
docker compose up --build                # 2. costruisce e avvia db + backend + frontend
```

Al primo avvio applica le migrazioni del database (con lo stack attivo):

```bash
docker compose exec backend uv run alembic upgrade head
```

Servizi disponibili:

| Servizio    | URL                                   |
| ----------- | ------------------------------------- |
| Frontend    | http://localhost:5173                 |
| Mood Tracker| http://localhost:5173/mood            |
| Backend API | http://localhost:8000                 |
| API docs    | http://localhost:8000/docs            |
| Healthcheck | http://localhost:8000/api/v1/health   |
| PostgreSQL  | localhost:5432                        |

Per fermare lo stack:

```bash
docker compose down        # mantiene i dati del database
docker compose down -v     # elimina anche il volume dati (pgdata)
```

---

## 6. Sviluppo locale (senza Docker)

### Backend

Dalla cartella `backend/`, in sequenza:

```bash
cd backend
cp .env.example .env                     # 1. configurazione (imposta DATABASE_HOST=localhost)
uv sync                                  # 2. crea il virtualenv e installa le dipendenze (Python 3.14)
uv run alembic upgrade head              # 3. crea/aggiorna lo schema del database
uv run uvicorn app.main:app --reload     # 4. avvia l'API su http://localhost:8000
```

### (Opzionale) Rigenerare i parametri pre-allenati

```bash
uv run python -m app.scripts.pretrain            # default: 30 turni/regime, seed 7
uv run python -m app.scripts.pretrain 50 42      # n_per_regime=50, seed=42
```

Lo script salva `app/engine/pretrained/noema_params.json` **solo** se la sanity
check finale supera il 75%; altrimenti esce con errore e i nuovi profili
useranno il modello vergine.

### Frontend

In un secondo terminale, dalla cartella `frontend/`:

```bash
cd frontend
npm install                              # 1. installa le dipendenze
npm run dev                              # 2. avvia su http://localhost:5173
```

In sviluppo le chiamate a `/api` vengono inoltrate al backend tramite il proxy
di Vite (`VITE_PROXY_TARGET`), evitando problemi di CORS.

---

## 7. Migrazioni database (Alembic)

Lo schema è gestito **esclusivamente** con Alembic (nessun `create_all`).
Comandi dalla cartella `backend/` (in locale) o via `docker compose exec backend …`:

```bash
uv run alembic upgrade head                        # applica tutte le migrazioni
uv run alembic revision --autogenerate -m "descr"  # genera una migrazione dai modelli
uv run alembic downgrade -1                        # rollback di un passo
```

Migrazioni presenti:

- `0001_create_users_table` — anagrafica utenti/profili;
- `0002_create_mood_tables` — `emotional_model_states` (parametri appresi, JSONB,
  un record per utente con *lock ottimistico*), `emotional_turns` (turni + stime),
  `emotional_feedback` (correzioni umane, con flag di consolidamento).

---

## 8. Configurazione

`backend/.env` è la **sorgente unica** di configurazione e **non è versionato**
(può contenere segreti). Va creato da `backend/.env.example`.

| Variabile           | Descrizione                                             |
| ------------------- | ------------------------------------------------------- |
| `APP_NAME`          | Nome dell'applicazione                                  |
| `APP_VERSION`       | Versione dell'applicazione                              |
| `DEBUG`             | Abilita il logging SQL / debug                          |
| `DATABASE_HOST`     | Host PostgreSQL (`localhost` in locale, `db` in Docker) |
| `DATABASE_PORT`     | Porta del database                                      |
| `DATABASE_NAME`     | Nome del database                                       |
| `DATABASE_USER`     | Utente del database                                     |
| `DATABASE_PASSWORD` | Password del database                                   |
| `STORE_TURN_TEXT`   | Se `true`, salva il testo grezzo dei turni; default `false` (privacy) |

Frontend (`frontend/.env`, opzionale):

| Variabile           | Descrizione                                          |
| ------------------- | ---------------------------------------------------- |
| `VITE_API_BASE_URL` | URL base delle API (default `/api/v1`)               |
| `VITE_PROXY_TARGET` | Target del proxy dev (in Docker `http://backend:8000`) |

> In Docker `DATABASE_HOST` viene forzato a `db` (nome del servizio) e i default
> del `docker-compose.yml` coincidono con `.env.example`: `docker compose up`
> funziona senza flag aggiuntivi. Cambiando le credenziali, ricrea il volume
> (`docker compose down -v`).

---

## 9. API principali

Tutti gli endpoint del dominio sono annidati sotto `/api/v1/users/{user_id}`.
Documentazione interattiva completa su `/docs`.

| Metodo | Endpoint | Descrizione |
| ------ | -------- | ----------- |
| `GET`  | `/api/v1/health` | Stato del backend |
| `GET/POST/PUT/DELETE` | `/api/v1/users` | CRUD dei profili |
| `POST` | `/users/{id}/turns` | **Ingest di un turno**: testo + segnali → stima emotiva |
| `GET`  | `/users/{id}/turns` | Storico dei turni |
| `GET`  | `/users/{id}/turns/{turn_id}` | Dettaglio di un turno |
| `POST` | `/users/{id}/turns/{turn_id}/feedback` | Conferma/correzione (solo sull'ultimo turno) |
| `GET`  | `/users/{id}/model` | Diagnostica del modello |
| `POST` | `/users/{id}/model/reset` | Riporta lo stato al baseline appreso |
| `POST` | `/users/{id}/calibrate` | Calibrazione con testo proprio (richiede consenso) |

---

## 10. Test e qualità (backend)

```bash
cd backend
uv run ruff check .           # lint
uv run ruff format --check .  # formattazione
uv run pytest                 # test (include la batteria dell'engine)
```

---

## 11. Integrazione continua

La pipeline GitHub Actions (`.github/workflows/ci.yml`) esegue a ogni push/PR:

- **backend**: install · lint (ruff) · test (pytest)
- **frontend**: install · build (con type-check `vue-tsc`)
- **docker**: build delle immagini backend e frontend (nessun push)

---

## 12. Struttura del progetto

```
mood_tracker/
├── backend/                     # API FastAPI (uv, SQLAlchemy, Alembic)
│   ├── app/
│   │   ├── api/                 # dependency (get_db) e router versionati (/api/v1)
│   │   │   └── v1/routes/       # endpoint: health, users, mood
│   │   ├── core/                # configurazione (pydantic-settings)
│   │   ├── db/                  # engine, session, Base declarative
│   │   ├── models/              # modelli SQLAlchemy (users, mood)
│   │   ├── schemas/             # schemi Pydantic (validazione I/O)
│   │   ├── repositories/        # accesso al database (turn, feedback, model_state)
│   │   ├── services/            # orchestrazione dominio (MoodService)
│   │   ├── scripts/             # pre-training offline
│   │   └── engine/              # ★ motore NOEMA (puro, testabile in isolamento)
│   │       ├── features.py      #   estrazione delle 24 feature
│   │       ├── matching.py      #   riconoscimento lessicale robusto
│   │       ├── model.py         #   dinamica di stato + apprendimento online
│   │       ├── emotions.py      #   spazio emotivo (8 emozioni + PAD)
│   │       ├── feedback.py      #   feedback supervisionato + consolidamento
│   │       ├── labels.py        #   descrizione testuale in italiano
│   │       ├── params.py        #   contenitore parametri serializzabile
│   │       ├── sanity.py        #   controlli di correttezza semantica
│   │       ├── pretrained/      #   asset dei parametri pre-allenati
│   │       └── lexicon/         #   lessico emotivo italiano (~488 voci)
│   ├── alembic/                 # migrazioni database
│   └── tests/                   # test (pytest)
├── frontend/                    # SPA Vue 3 + TypeScript (Vite)
│   └── src/                     # router, stores (Pinia), services, composables, views
├── docker-compose.yml           # orchestrazione db + backend + frontend
└── .github/workflows/           # CI
```

---

## 13. Nota etica e sulla privacy

- **Consenso**: la calibrazione va usata solo con testo scritto dalla stessa
  persona monitorata (vincolo imposto anche a livello di API).
- **Minimizzazione dei dati**: `STORE_TURN_TEXT=false` (default) salva solo
  feature ed esiti, mai il testo grezzo dei messaggi.
- **Onestà metodologica**: il lessico è costruito a mano e non validato
  psicometricamente; le coordinate PAD sono illustrative. Ogni stima riporta la
  confidenza e un disclaimer, e segnala esplicitamente quando nessuna parola è
  stata riconosciuta nel lessico.

---

## 14. Licenza

[MIT](LICENSE) © 2026 Massimo Dell'Erba
