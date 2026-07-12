Questo codice rappresenta il prototipo originale dell'algoritmo.

Non fa parte dell'applicazione.

Serve esclusivamente come riferimento per comprenderne la logica e ricostruire una nuova implementazione all'interno dell'architettura FastAPI + Vue.

Non copiare il codice direttamente nell'applicazione.

# NOEMA — tracciamento sperimentale dello stato emotivo

Sistema dinamico adattivo (non rete neurale) per stimare lo stato emotivo da testo italiano, dinamica di digitazione e feedback umano. Prototipo di ricerca — leggi [`POSIZIONAMENTO.md`](POSIZIONAMENTO.md) e [`NOEMA_documentazione.md`](NOEMA_documentazione.md) prima di un uso reale.

## Avvio rapido

```bash
pip install -r requirements.txt
python3 -m pytest test_noema.py -v   # verifica che tutto funzioni (47 test)
python3 main.py                       # applicazione interattiva
```

Al primo avvio, `main.py` carica automaticamente `noema_params.json` (parametri pre-allenati) se presente — consigliato rispetto a partire da un modello vergine.

## File principali

| File | Cosa fa |
|---|---|
| `main.py` | Applicazione interattiva: scrivi messaggi, cattura tempi di digitazione reali, dai feedback |
| `noema.py` | Modello: stato a 8 dimensioni, dinamica adattiva, feedback, demone |
| `lessico_italiano.py` | Vocabolario emotivo (488 voci: formale, colloquiale, slang) |
| `test_noema.py` | Suite di test automatici (47 test) |
| `train.py` / `evaluate.py` | Training e valutazione onesta su dati mai visti |
| `generate_training_data.py` | Genera dataset sintetici di training |
| `noema_params.json` | Parametri già allenati, pronti all'uso |

## Uso come libreria

```python
from noema import NoemaDaemon

daemon = NoemaDaemon(params_path="noema_params.json")
record = daemon.ingest_turn(
    text="sono molto felice oggi",
    keydown_times=[0.1, 0.2, 0.3],   # timestamp di ogni tasto premuto
    backspace_count=0,
    response_latency_s=3.5,
    is_followup=False,
    followup_depth=0,
)
print(record["label"])  # descrizione testuale italiana

daemon.provide_feedback(corretto=True)  # o corretto=False, emozione_corretta="gioia"
```

## Documenti

- **[NOEMA_documentazione.md](NOEMA_documentazione.md)** — architettura completa, matematica, cronistoria onesta di tutti i bug trovati e corretti
- **[POSIZIONAMENTO.md](POSIZIONAMENTO.md)** — cosa questo sistema offre di diverso rispetto a librerie di sentiment analysis e modelli commerciali, e dove invece resta indietro
- **[PRIVACY.md](PRIVACY.md)** — che dati vengono raccolti, dove restano, come cancellarli

## Limite più importante

Mai validato su dati umani reali con misure di riferimento indipendenti. È un prototipo di ricerca, non uno strumento diagnostico. Vedi `NOEMA_documentazione.md` §8.
