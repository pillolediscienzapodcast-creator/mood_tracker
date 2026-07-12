# NOEMA v0.4 — Documentazione completa

*Modello matematico auto-adattivo per la stima continua dello stato emotivo, con personalizzazione via feedback*

---

## 0. Prima di tutto: tre chiarimenti onesti

Questa versione è stata esplicitamente richiesta come "intelligenza artificiale evoluta, senza se e senza ma" e "non presente in letteratura". Prima dei dettagli tecnici, tre punti fermi:

**È "IA"?** Nel senso ampio/storico sì: è un sistema adattivo che modifica il proprio comportamento in base ai dati (cibernetica, controllo adattivo, filtraggio bayesiano sono storicamente parte dell'intelligenza artificiale). **Non è deep learning, non è un LLM** — è un'alternativa deliberata a quello, costruita apposta per non usare reti neurali, come richiesto. Il codice e l'architettura sono più ricchi ed elaborati rispetto alle versioni precedenti di questa conversazione — questo è un fatto verificabile nel codice — ma l'etichetta va giudicata sulla sostanza, non dichiarata per decreto.

**È "non presente in letteratura"?** È una combinazione originale di tecniche esistenti (sistemi dinamici, RLS, predictive coding, Plutchik/PAD) applicata in modo non standard a questo problema. Nessuno può onestamente garantire l'assenza totale di precedenti in letteratura senza una revisione sistematica — non lo farò con un'affermazione che non posso verificare.

**È "vendibile e affidabile"?** Il codice è ora più robusto, meglio testato, con controlli di sicurezza automatici (vedi §5). Ma "affidabile" in senso pieno richiede validazione su dati umani reali con misure di riferimento indipendenti — nessuna quantità di lavoro sul codice sostituisce quella fase (vedi §8). Questa versione include inoltre una scelta di design deliberata: **non raccoglie né elabora profili social/LinkedIn/pubblicazioni di terzi** per dedurne lo stato psicologico, anche se richiesto. Costruire un sistema che profila persone a partire da contenuti pubblici, specialmente su chi non sta interagendo attivamente con lo strumento, è il tipo di funzionalità che abilita sorveglianza, stalking o discriminazione senza consenso. L'alternativa implementata (§4.5) rispetta il consenso: solo la persona monitorata può fornire testo scritto da lei stessa per calibrare il modello.

---

## 1. Cosa è cambiato rispetto alla versione precedente

| Aspetto | Prima | Ora |
|---|---|---|
| Stato emotivo | 3 dimensioni (Valenza/Arousal/Dominanza) | **8 dimensioni** (emozioni di base di Plutchik: gioia, fiducia, paura, sorpresa, tristezza, disgusto, rabbia, anticipazione) + PAD derivato come riassunto |
| Feature di input | 14, lessico italiano di ~20 parole | **24 feature**, lessico di ~150 voci con negazione, intensificatori, suffissi superlativi, emoji, auto-focus pronominale |
| Parametri totali | ~99 (K, B, C, z0) | **~600+** (K: 8, z0: 8, B: 8×24=192, C: 24×8=192, P: 8×8=64, più le statistiche di normalizzazione personale) |
| Personalizzazione | Solo auto-supervisionata (predictive coding) | Auto-supervisionata **+ feedback umano supervisionato** con consolidamento periodico |
| Output testuale | Etichetta fissa breve | **Descrizione italiana generata dinamicamente** dai valori numerici, con hedging sulla confidenza |
| Controlli di qualità | Nessuno strutturale | **Batteria di controlli di correttezza semantica**, eseguita automaticamente dopo ogni training, con blocco del salvataggio se il punteggio è insufficiente |
| Applicazione | Solo libreria | **`main.py`**: app da riga di comando con cattura reale dei tempi di digitazione e ciclo di feedback |

---

## 2. Lo spazio degli stati: 8 emozioni di base + PAD derivato

Invece di rappresentare solo Valenza/Arousal/Dominanza, lo stato ora è un vettore a 8 dimensioni — una per ciascuna delle emozioni di base del modello di Plutchik: **gioia, fiducia, paura, sorpresa, tristezza, disgusto, rabbia, anticipazione**.

Ogni asse ha un'intensità in (0,1) tramite sigmoide: 0.5 = assente/neutro, verso 1 = massima intensità. Valenza/Arousal/Dominanza (PAD) restano disponibili ma sono ora **derivate** come combinazione pesata dello scostamento dal neutro di ciascuna emozione, secondo coordinate approssimative standard in letteratura di affective computing (circumplex di Russell, ruota di Plutchik) — valori illustrativi, non costanti psicometriche precise.

Questo è un aumento reale di espressività: il sistema può ora rappresentare stati **misti** (es. "rabbia e tristezza insieme", tipico della frustrazione) che tre soli assi PAD comprimono in un unico punto, perdendo l'informazione su quale combinazione specifica di emozioni li produce.

---

## 3. Feature linguistiche italiane — molto più ricche

Il lessico (`lessico_italiano.py`) è passato da ~20 a **~150 voci**, organizzate sulle 8 emozioni, con gestione di:

- **Negazione**: "non sono felice" attenua/inverte il contributo della parola emotiva (finestra di 3 token precedenti). Nota onesta: non equivale linguisticamente a "sono triste" — è un'attenuazione, non uno specchio, e resta un'area di incertezza del modello (vedi §7).
- **Intensificatori/diminutori**: "molto", "davvero", "estremamente" amplificano; "poco", "leggermente" attenuano.
- **Suffissi superlativi**: "tristissimo", "felicissimo" pesano di più della forma base.
- **Emoji/emoticon**: un piccolo dizionario dedicato (😊😢😡😱 ecc.) contribuisce alla stima.
- **Auto-focus pronominale**: rapporto fra pronomi in prima persona singolare e plurale/altri — un correlato linguistico discusso in letteratura psicolinguistica (Pennebaker e altri), qui trattato esplicitamente come segnale debole fra tanti, non come prova.
- **Enfasi da ripetizione**: lettere ripetute ("nooo", "grazieee") come proxy di enfasi.

**Onestà metodologica**: resta un lessico dimostrativo costruito a mano, non una risorsa validata psicometricamente su larga scala (a differenza di NRC-VAD o LIWC). Copre alcune centinaia di forme comuni, non l'intero vocabolario emotivo italiano.

---

## 4. Auto-parametrizzazione, personalizzazione, e feedback

### 4.1 Il nucleo (invariato nello spirito, generalizzato nella dimensione)

Stessa equazione di stato (sistema dinamico stocastico + RLS per la mappa generativa C + discesa a gradiente con leakage per B), ora in 8 dimensioni invece di 3. La matematica di fondo non è cambiata concettualmente — è stata estesa a una rappresentazione più ricca, con tutte le implicazioni di stabilità che questo comporta (vedi §7).

### 4.2 Normalizzazione personale online

Il modello traccia media e varianza (algoritmo di Welford) della velocità di digitazione **di quella specifica persona**, usata per calcolare `typing_speed_relative`: "digitare veloce" ha senso relativamente al proprio ritmo abituale, non a una soglia identica per chiunque.

### 4.3 Feedback supervisionato — il meccanismo di rinforzo richiesto

Dopo ogni stima, la persona che monitora può rispondere se è corretta o no (e, se no, indicare l'emozione giusta fra le 8). Questo:

1. **Corregge subito** lo stato corrente (misura Bayesiana: sposta la stima verso il target indicato, non un reset completo).
2. **Si accumula in un buffer** per un consolidamento periodico.

### 4.4 Consolidamento periodico — ogni 5 feedback

Il consolidamento (`consolidate_feedback()`) rielabora i feedback accumulati aggiornando B e C usando i target **forniti dall'umano** invece dell'auto-predizione — una correzione supervisionata con peso maggiore di un passo online ordinario.

**Perché ogni 5 e non ad ogni feedback o ogni 20?** È una dimensione di mini-batch comune nell'apprendimento online: abbastanza piccola da restare reattiva a una persona nuova (non aspetta 20 turni per correggersi), abbastanza grande da mediare il rumore di un singolo giudizio umano (un feedback isolato potrebbe essere impreciso quanto il modello). Il valore è configurabile (`consolidation_every` nel costruttore di `NoemaModel`).

### 4.5 Calibrazione con testo proprio — l'alternativa allo scraping social

Il modello richiesto includeva la possibilità di usare pubblicazioni scientifiche, profili LinkedIn/social per "far capire all'algoritmo chi è l'utente". **Questa funzionalità non è stata implementata come richiesto** — vedi §0. È stata sostituita da `NoemaDaemon.calibra_con_testo()`, disponibile anche interattivamente in `main.py`: la persona monitorata può incollare testo scritto da lei stessa (bio, post, articoli) per una calibrazione iniziale, con un controllo esplicito nel codice che impedisce l'uso accidentale su testo di terzi (`autore_e_soggetto_coincidono`).

---

## 5. Controlli di correttezza semantica — la difesa contro un problema reale

Nella versione precedente di questo progetto, ottimizzare la metrica astratta di predizione ha degradato la correttezza: il modello arrivò a interpretare "sono molto arrabbiato" come valenza positiva. Questa versione include una difesa strutturale contro il ripetersi del problema:

- **`SANITY_CHECKS`**: batteria di 12 frasi italiane con emozione dominante attesa nota (una per ciascuna delle 8 emozioni, più casi di negazione e superlativi).
- **`run_sanity_checks()`**: le esegue in modalità sola-inferenza (non altera i parametri), riporta la frazione corretta.
- **`train.py` blocca il salvataggio** se il punteggio dopo il training scende sotto il 75%, con un messaggio esplicito — a meno di forzare con `--forza`.

Risultato attuale (vedi anche §6): **92%** (11/12) sia prima che dopo il training — il pre-training non ha degradato la correttezza semantica, a differenza della volta precedente.

### Cronistoria onesta dei bug trovati DURANTE questa sessione di sviluppo

Costruire la versione a 8 dimensioni non è stato lineare. In ordine:

1. **Contaminazione fra controlli**: `run_sanity_checks` non azzerava lo stato fra una frase e l'altra, facendo "ereditare" a ogni frase il risultato della precedente. Corretto: ogni prova riparte dal baseline.
2. **Soglia di dominanza tarata male**: con la sigmoide il punto neutro è 0.5 (non 0 come con tanh); la vecchia soglia era sostanzialmente inefficace. Ricalibrata sui valori realmente osservabili in un singolo turno.
3. **Instabilità numerica in 8 dimensioni**: con gli iperparametri della versione a 3 dimensioni, l'errore di predizione **aumentava** durante il training invece di scendere. Causa: la normalizzazione online personale trasformava l'INTERO vettore di feature ad ogni turno, creando un bersaglio di predizione "in movimento" per la RLS. Corretto: la normalizzazione ora alimenta solo una feature dedicata (`typing_speed_relative`), senza deformare l'intero spazio di input.
4. **Collasso su un singolo asse ("tristezza", poi "paura")**: feature sempre presenti e sempre positive (es. `response_latency`, mai negativa) collegate nel prior a un singolo asse emotivo lo spingevano sistematicamente verso l'alto turno dopo turno, indipendentemente dal contenuto. Corretto con due misure: centratura di alcune feature attorno a un valore neutro plausibile invece che zero, e una regolarizzazione che tira ogni asse del baseline verso la MEDIA degli altri assi (non solo verso zero) — impedisce strutturalmente che un singolo asse "scappi dal gruppo".
5. **Correlazione spuria digitazione-emozione**: il dataset sintetico aveva la digitazione più veloce artificialmente confinata al regime "rabbia", che il modello ha imparato correttamente come scorciatoia — corretta aggiungendo rumore che sovrappone le velocità di digitazione fra regimi, cosicché il contenuto lessicale resti il segnale primario.
6. **Bug nel calcolo di PAD**: la formula usava l'intensità grezza (0.5=neutro) invece dello scostamento dal neutro, facendo risultare l'Arousal quasi sempre vicino a +1 anche per testi neutri. Corretto.

Li riporto tutti perché fanno parte di cosa significa concretamente "affidabile": non è un'affermazione, è un processo verificabile.

---

## 5bis. Seconda cronistoria di bug — scoperti dall'uso reale (non dai test sintetici)

Dopo la prima consegna, un uso reale con `main.py` ha mostrato risposte chiaramente sbagliate ("felicissimo" letto come tristezza/rabbia) nonostante i test automatici dessero 92%. Motivo: i test sintetici non esercitavano alcune combinazioni che l'uso reale incontra subito. In ordine:

1. **Tokenizzazione fragile**: `"felicissimo!!!!+"` non veniva riconosciuta affatto — il simbolo finale "+" non era nell'elenco di caratteri da rimuovere, quindi l'intera parola restava non identificata e il lessico non veniva mai consultato. Corretto con una tokenizzazione a base di espressione regolare (estrae solo lettere, ignora qualunque punteggiatura/simbolo circostante, non solo quelli previsti in anticipo).
2. **Reattivita' troppo bassa**: anche dopo il fix, un segnale fortissimo e inequivocabile spostava la stima solo di pochi punti percentuali. Corretto aumentando il passo di integrazione (dt) e riducendo l'incertezza iniziale della RLS (P0_scale), che insieme rendono la confidenza iniziale meno punitiva e la risposta piu' decisa a segnali chiari.
3. **Bug di unita' di misura in `typing_speed_relative`**: la baseline personale di velocita' di digitazione veniva confrontata in un'unita' (grezza, tasti/secondo) diversa da quella in cui era stata effettivamente calcolata (scalata/centrata) — un errore classico di conversione che produceva SEMPRE il valore estremo (+4, il massimo), indipendentemente da quanto una persona digitasse davvero velocemente. Questo, propagato tramite il collegamento della feature con rabbia/paura/sorpresa, causava un'attivazione artificiale costante di quei tre assi. Corretto riconvertendo correttamente le unita'.
4. **Pesi spuri su feature non intenzionali**: `circadian_phase` (fase del giorno) aveva sviluppato durante il training un peso di -0.42 su "sorpresa" — una connessione che non avevo mai previsto nel prior, emersa spontaneamente per rumore casuale amplificato dal ciclo di adattamento. Dato che il valore dipende dall'ora reale in cui si usa il programma (diversa da quella usata nei test sintetici), questo produceva risultati diversi e sbagliati a seconda di che ora fosse. Corretto strutturalmente: una maschera esplicita distingue le connessioni DELIBERATE del prior (lessico, cluster di attivazione) dalle altre, e solo le prime mantengono piena liberta' di adattamento — le altre restano vincolate molto piu' vicino a zero, indipendentemente dal rumore casuale iniziale.

**Limite residuo, dichiarato onestamente**: in una conversazione continua di piu' turni, un messaggio chiaramente arrabbiato dopo alcuni turni "neutri/riflessivi" a volte non mostra ancora "rabbia" come prima emozione in classifica (compare comunque, ma non sempre al primo posto) — probabilmente inerzia cumulata dai turni precedenti combinata con l'attivazione generica condivisa fra rabbia/paura/disgusto. Non l'ho forzato con altre patch mirate: la correzione strutturale del punto 4 e' piu' robusta di un ennesimo aggiustamento puntuale, e il meccanismo di feedback (§4.3-4.4) e' pensato apposta per correggere casi come questo con l'uso.

---

## 5ter. Terza cronistoria — copertura del lessico e default di avvio

Un altro test reale ha mostrato "sono molto emozionato" letto come neutro, con confidenza sempre bassa. Causa reale, diversa dalle precedenti: **la parola "emozionato" semplicemente non era nel lessico** (182 voci nella versione precedente) — nessun bug di calcolo, solo una copertura lessicale insufficiente per l'uso quotidiano. In più, `main.py` avviava di default un modello completamente vergine invece dei parametri pre-allenati forniti, aggravando il problema di bassa confidenza per chi non specificava esplicitamente `--profilo` con un file già allenato.

Corretto con tre interventi:
1. **Lessico quasi raddoppiato** (182 → 279 voci): aggiunte parole comuni della vita quotidiana mancanti (emozionato, commosso, motivato, geloso, confuso, sollevato, stufo, e molte altre).
2. **`main.py` ora carica di default `noema_params.json`** (se presente nella cartella) per qualunque profilo nuovo, invece di partire da un modello vergine — un modello mai allenato ha confidenza strutturalmente bassa e riconosce molto meno.
3. **Nota di trasparenza dedicata**: quando nessuna parola del messaggio è nel lessico (es. "ciao"), l'output lo dice esplicitamente invece di lasciare un generico avviso di bassa confidenza — chi legge deve poter distinguere "il testo non conteneva contenuto emotivo riconoscibile" da "il modello non funziona".

**Limite onesto, ancora presente**: 279 voci restano una frazione minima del vocabolario emotivo italiano reale. Frasi con vocabolario comune ma non incluso continueranno a risultare "neutre" o poco informative. Non esiste, in questa architettura, una soluzione definitiva a questo se non ampliare ulteriormente il lessico (manualmente o integrando una risorsa linguistica validata più ampia) — è un limite strutturale di un lessico costruito a mano, dichiarato fin dalla prima versione di questo documento.

---

## 5quater. Espansione slang e linguaggio colloquiale

Il lessico è passato da 279 a **355 voci**, con un blocco dedicato a slang, esclamazioni informali e termini volgari di uso comune (es. "figata", "pazzesco", "cazzo", "minchia", "vaffanculo", "sbroccare", "depre"), necessario perché nel testo reale le persone esprimono emozioni forti anche così, non solo in italiano formale. Sono stati aggiunti anche negatori colloquiali mancanti ("manco", "mica", "nn", "neanche", "nemmeno") e alcuni intensificatori gergali ("mega", "assai", "bestiale").

**Criterio seguito**: incluse solo espressioni volgari generiche (esclamazioni, intensificatori emotivi di uso corrente) — mai termini offensivi rivolti a persone, gruppi o identità specifiche.

Verificato che l'espansione non cambia il punteggio di correttezza semantica (92%, invariato) e che le nuove parole vengono riconosciute correttamente quando valutate come turno indipendente. In una conversazione lunga, l'inerzia fra turni (§4, §5bis) può ancora attenuare il segnale di un singolo messaggio gergale se i turni precedenti avevano un tono diverso — comportamento della dinamica, non del lessico.

---

## 5quinquies. Copertura completa e gestione della scrittura non standard

Il lessico è passato da 355 a **488 voci**, con due interventi distinti:

**1. Vocabolario comune quotidiano** (131 voci nuove): verbi, sostantivi e aggettivi di uso normale mancanti — "piacere", "dolore", "soffrire", "stress", "successo", "pace", "litigare", e molti altri. In questo passaggio sono anche emerse mancanti, sorprendentemente, le parole **"tristezza" e "anticipazione" stesse** — due delle otto emozioni di base non erano riconosciute come parole proprie. Corrette.

**2. Riconoscimento di scrittura non standard**: la tokenizzazione precedente *spezzava* parole contenenti asterischi o cifre (es. "ca\*\*o" diventava due frammenti irriconoscibili "ca" e "o", prima ancora di arrivare al lessico). Corretto con una pipeline di normalizzazione in `noema.py` che prova, in ordine: corrispondenza esatta → lettere ripetute collassate ("grazieee"→"grazie") → sostituzione leet numero/lettera ("c4zzo"→"cazzo") → "k" informale al posto di "c" ("kazzo"→"cazzo") → corrispondenza jolly per censure con asterischi ("ca\*\*o"→"cazzo"), quest'ultima accettata solo se univoca o se l'unica parola candidata è fra quelle tipicamente censurate nella scrittura reale (altrimenti, es. "ca\*\*o" sarebbe ambiguo fra "cazzo" e "calmo": si evita di indovinare).

**Limite onesto, non ancora risolto**: gli intensificatori ("molto", "tantissimo"...) vengono riconosciuti solo se precedono la parola emotiva ("sono molto felice"), non se la seguono ("mi piace tantissimo") — la finestra di contesto guarda solo indietro. Una correzione richiederebbe estendere la finestra anche in avanti; non l'ho fatto in questo passaggio perché non era l'ambito della richiesta, ma è un miglioramento naturale per una prossima iterazione.

---

## 5sexies. Ultimo giro: qualità del prodotto, non solo del modello

Su richiesta esplicita di rendere il progetto vendibile e affidabile "ad alto valore aggiunto", sono stati aggiunti quattro elementi che non riguardano la matematica del modello ma la qualità del prodotto nel suo complesso:

1. **Suite di test automatici** (`test_noema.py`, 47 test, `pytest`): copre estrazione feature, normalizzazione di scrittura non standard, dinamica del modello, persistenza, feedback, robustezza a input anomali, stabilità numerica su 500 turni consecutivi, e il controllo di correttezza semantica come vero test automatico (non solo uno script da lanciare a mano). Un test ha scoperto un bug nel test stesso (riferimento a un oggetto stato mutabile confrontato con se stesso), corretto e documentato nel codice.
2. **Fix di un limite noto**: gli intensificatori ("tantissimo", "molto"...) ora vengono riconosciuti anche se seguono la parola emotiva ("piace tantissimo"), non solo se la precedono. La negazione resta intenzionalmente solo all'indietro, per motivi grammaticali (vedi commento nel codice).
3. **`POSIZIONAMENTO.md`**: confronto onesto con lessici statici, modelli transformer italiani e API commerciali — vantaggi reali (trasparenza, nessun dato che lascia il dispositivo, personalizzazione via feedback, segnali multimodali) e limiti reali (accuratezza grezza quasi certamente inferiore a un modello allenato su grandi corpora, nessuna comprensione contestuale, mai validato su dati umani).
4. **`PRIVACY.md`**: cosa viene raccolto, dove resta, come cancellarlo, requisiti di consenso.

Questi non sostituiscono la validazione umana ancora mancante (§8): sono la parte di "affidabilità" che il codice può effettivamente garantire da solo, resa verificabile e ripetibile invece che affermata.

---

## 5septies. Stemming e frasi idiomatiche

Le due debolezze discusse esplicitamente con l'utente — copertura lessicale limitata alle forme elencate, e nessuna comprensione di espressioni multi-parola — sono state affrontate nei limiti di quanto possibile senza reti neurali:

**Stemming morfologico**: integrato lo stemmer italiano di Snowball (via `nltk`, puramente algoritmico, nessun download di dati necessario). Un indice radice→emozione viene costruito una sola volta dal lessico esistente; quando una parola non trova corrispondenza esatta (né tramite le normalizzazioni già presenti), viene ridotta alla radice e cercata in quell'indice. Questo riconosce automaticamente coniugazioni verbali non elencate esplicitamente ("arrabbiava", "arrabbiarsi", "arrabbieranno" → tutte ricondotte a "arrabbiato", già nel lessico) senza dover elencare ogni forma a mano. **Limite onesto**: lo stemmer italiano non unifica bene tutte le famiglie di parole — "triste" e "tristezza" producono radici diverse ("trist" vs "tristezz"), quindi resta utile avere entrambe le forme esplicite nel lessico per le parole più importanti. È un aiuto, non una soluzione completa.

**Frasi idiomatiche**: 19 espressioni comuni (2-4 parole) riconosciute come unità prima della scomposizione a singola parola — "non vedo l'ora", "che due palle", "sono a pezzi", "in bocca al lupo", ecc. Necessario perché la somma delle parole singole darebbe risultati sbagliati: "non vedo l'ora" contiene "non" ma non è affatto una negazione.

**Cosa resta fuori portata, dichiarato senza girarci intorno**: comprensione sintattica reale (capire *cosa* nega una negazione in una frase complessa), sarcasmo, ironia. Questi richiederebbero embedding semantici o un modello linguistico pre-addestrato — a quel punto si uscirebbe dal vincolo "niente reti neurali" posto fin dall'inizio di questo progetto. Non c'è una scorciatoia simbolica che replichi quella capacità.

---

## 6. Risultati misurati (su dati sintetici — vedi limiti in §8)

```
Controllo di correttezza semantica: 92% (11/12) prima E dopo il training
Errore di predizione su dati mai visti: -13.4% (modello pre-allenato vs vergine)
```

Il miglioramento nella predizione **non** è arrivato a scapito della correttezza semantica, a differenza della versione precedente — i due numeri ora si muovono insieme, non l'uno contro l'altro.

---

## 7. Limiti onesti di questa versione specifica

- **La negazione resta un punto debole**: "non sono per niente felice" non viene sempre classificata correttamente (nel test attuale, risulta "anticipazione" invece di "tristezza"). Linguisticamente, la negazione di un'emozione positiva non equivale in modo affidabile a un'emozione negativa specifica — è un'area di incertezza reale, non solo un bug da correggere con più dati.
- **Il lessico resta artigianale** (~150 voci), non una risorsa validata su larga scala.
- **8 dimensioni + 24 feature = più parametri da stimare con pochi dati**: la maggiore espressività ha un costo in termini di dati necessari per una stima affidabile — il feedback umano (§4.3) è pensato apposta per compensare, ma richiede che la persona lo fornisca con costanza.
- **Nessuna validazione su dati umani reali**: tutto quanto sopra è dimostrato su dati sintetici. Resta il limite più importante, invariato dalle versioni precedenti.

---

## 8. Validazione — cosa servirebbe per un vero prodotto affidabile

Invariato dalla versione precedente, e ancora il passaggio più importante: confronto sistematico con autovalutazioni reali (PANAS o simili), test-retest, validità predittiva rispetto a eventi osservabili indipendentemente. Nessuna quantità di lavoro sul codice sostituisce questa fase.

---

## 9. File inclusi

| File | Contenuto |
|---|---|
| `noema.py` | Modulo principale: stato a 8 dimensioni, feature linguistiche, nucleo adattivo (RLS + gradiente con leakage), feedback supervisionato, sanity check, demone |
| `lessico_italiano.py` | Lessico emotivo (~150 voci), negazione, intensificatori, emoji, coordinate PAD |
| `generate_training_data.py` | Genera dataset sintetici (training/validation/test) in JSONL |
| `training_data.jsonl` | 240 turni sintetici per il training (seed=7) |
| `validation_data.jsonl` | 120 turni per eventuale tuning (seed=55) |
| `test_data.jsonl` | 64 turni di test mai usati in training (seed=99) |
| `train.py` | Training con controllo di correttezza semantica automatico e gate di sicurezza |
| `evaluate.py` | Valutazione onesta: vergine vs pre-allenato, su dati mai visti |
| `noema_params.json` | Parametri già allenati inclusi in questa consegna |
| `demo.py` | Test dimostrativo con grafico delle 8 traiettorie emotive |
| `noema_demo.png` / `training_curve.png` | Grafici generati |
| `main.py` | **Applicazione interattiva**: cattura tempi di digitazione reali, ciclo di feedback, profili per utente |
| `test_noema.py` | Suite di test automatici (47 test, `pytest`) |
| `README.md` | Porta d'ingresso rapida al progetto |
| `POSIZIONAMENTO.md` | Confronto onesto con alternative di mercato/letteratura |
| `PRIVACY.md` | Gestione dei dati e requisiti di consenso |
| `requirements.txt` | Dipendenze Python |

---

## 10. Istruzioni — dal training all'uso quotidiano

### 10.1 Preparazione (una volta sola)

```bash
pip install numpy matplotlib
```

Metti tutti i file scaricati nella stessa cartella.

### 10.2 (Ri)generare i dati sintetici — opzionale, sono già inclusi

```bash
python3 generate_training_data.py 30 training_data.jsonl 7
python3 generate_training_data.py 8 test_data.jsonl 99
```

### 10.3 Allenare il modello

```bash
python3 train.py training_data.jsonl noema_params.json
```

Esegue il training, il controllo di correttezza semantica prima/dopo, e salva solo se il punteggio resta sopra il 75% (altrimenti spiega perché e si ferma).

### 10.4 Verificare onestamente la qualità

```bash
python3 evaluate.py noema_params.json test_data.jsonl
```

### 10.5 Usarlo interattivamente — l'applicazione principale

```bash
python3 main.py --profilo iltuonome
```

- Scrivi messaggi liberamente: i tempi di digitazione vengono catturati automaticamente (solo di questo prompt).
- Dopo ogni stima, puoi confermarla o correggerla — il modello impara da questo.
- Il profilo si salva automaticamente ogni 10 turni e all'uscita (`exit`).
- Comandi: `diagnostica` (stato interno del modello), `aiuto`.
- Al primo avvio di un profilo nuovo, puoi fornire un testo scritto da te stesso per calibrare il modello prima di iniziare (§4.5) — premi 'n' per saltare questo passaggio.

Ogni profilo (`--profilo nome`) mantiene parametri separati in `profili/nome.json`, così più persone possono usare lo strumento sullo stesso computer senza mescolare i dati (sempre con il consenso di ciascuna).

### 10.6 Integrarlo in un'applicazione propria

```python
from noema import NoemaDaemon

daemon = NoemaDaemon(params_path="noema_params.json", log_path="log.jsonl")
record = daemon.ingest_turn(
    text="...", keydown_times=[...], backspace_count=0,
    response_latency_s=4.5, is_followup=True, followup_depth=1,
)
print(record["label"])  # descrizione testuale italiana completa

daemon.provide_feedback(corretto=False, emozione_corretta="tristezza")
```
