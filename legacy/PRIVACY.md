# Gestione dei dati e privacy

## Cosa viene raccolto

Ad ogni turno di interazione (`ingest_turn`), il sistema elabora:
- il testo scritto dall'utente
- i timestamp di ciascun tasto premuto **in quel singolo messaggio, in quel prompt** (non un keylogger globale: non vede nulla digitato fuori dall'applicazione)
- metadati del turno (numero di correzioni, tempo di risposta, ora del giorno)

## Dove restano i dati

- **Tutta l'elaborazione avviene localmente.** Nessuna chiamata di rete, nessun dato inviato altrove.
- `main.py` salva, per ciascun profilo (`--profilo nome`), un file `profili/nome.json` con i **parametri appresi** (numeri: matrici, vettori) — non il testo dei messaggi.
- Se si passa `log_path` a `NoemaDaemon`, ogni stima (incluso il testo originale del messaggio) viene scritta in un file `.jsonl` in chiaro, in locale. Questo è **opzionale** e disattivato di default in `main.py`.

## Cosa NON fa questo sistema

- Non invia dati a server esterni.
- Non raccoglie né elabora contenuti da profili social, LinkedIn o pubblicazioni di terzi (scelta di design deliberata — vedi `NOEMA_documentazione.md` §0).
- Non traccia la digitazione al di fuori del prompt dell'applicazione.

## Come cancellare i dati

- Cancellare il file `profili/nome.json` rimuove tutti i parametri appresi per quel profilo.
- Cancellare l'eventuale file di log (`.jsonl`, se attivato) rimuove la cronologia dei messaggi.
- Non esiste, in questa versione, una funzione di cancellazione integrata nell'interfaccia — è manuale (cancellazione dei file). Per un prodotto reale con più utenti, aggiungere un comando esplicito di cancellazione/export dei dati (diritto all'oblio, portabilità) è un requisito, non un optional, se il contesto d'uso ricade sotto GDPR o normative equivalenti.

## Consenso

Questo sistema raccoglie dati comportamentali potenzialmente sensibili (contenuto emotivo del testo scritto, pattern di digitazione). Va usato:
- solo su se stessi, oppure
- con il consenso esplicito e informato della persona monitorata, che deve sapere cosa viene raccolto, dove resta, e come viene usato.

Non è progettato, e non deve essere adattato, per il monitoraggio di persone a loro insaputa.

## Limite dichiarato

Questo documento descrive il comportamento del codice così com'è fornito. Non costituisce una valutazione legale di conformità GDPR o altre normative — per un uso commerciale reale, una revisione legale specifica per la giurisdizione e il contesto d'uso resta necessaria.
