# Posizionamento di NOEMA rispetto a letteratura e mercato

Questo documento risponde direttamente a una domanda legittima: cosa offre questo sistema che altri non offrono, e dove invece è più debole? Non è un confronto empirico misurato fianco a fianco con altri sistemi (non ho i mezzi per farlo in questo ambiente) — sono considerazioni fattuali basate sulle proprietà note di ciascun approccio. Dove non sono certo, lo dico.

## Le alternative reali sul mercato/in letteratura

1. **Lessici statici di sentiment/emotion** (es. NRC-VAD, LIWC, risorse accademiche italiane come SentIta/Sentipolc): dizionari parola→punteggio, senza adattamento, senza personalizzazione, senza segnali comportamentali oltre al testo.
2. **Modelli transformer allenati per l'italiano** (es. varianti di BERT/RoBERTa italiane fine-tuned per sentiment/emotion, come i modelli emersi da EVALITA o il modello FEEL-IT): reti neurali allenate su migliaia/milioni di esempi etichettati.
3. **API commerciali di emotion AI** (es. servizi cloud di analisi del sentiment, piattaforme di "emotion AI" multimodali): servizi in abbonamento, elaborazione lato server.

## Dove NOEMA ha un vantaggio reale

- **Trasparenza totale**: ogni numero in output è ricostruibile a mano — quale parola ha contribuito, con che peso, attraverso quale equazione. Un modello transformer non offre questo: puoi ispezionare l'attenzione ma non "spiegare" una previsione nel modo in cui puoi tracciare `B[rabbia, lex_rabbia] × 0.8 → drift → z_pred`. Per contesti che richiedono auditabilità (ricerca, strumenti educativi su AI interpretabile) è un vantaggio concreto, non teorico.
- **Nessun dato lascia il dispositivo**: a differenza delle API commerciali via cloud, tutta l'elaborazione avviene localmente. Non è un vantaggio esclusivo del non usare reti neurali (un modello locale open-source avrebbe la stessa proprietà), ma è reale rispetto a qualunque servizio basato su API esterna.
- **Nessun bisogno di GPU o dataset enormi**: si allena in secondi su CPU con 240 esempi sintetici. Il fine-tuning di un transformer richiede infrastruttura e dati che un singolo sviluppatore spesso non ha.
- **Personalizzazione continua via feedback esplicito**: il meccanismo di correzione supervisionata (§4.3-4.4 del documento teorico) adatta il modello a una persona specifica da un singolo giudizio umano, senza dover ri-allenare un intero modello. Personalizzare un transformer per singolo utente in tempo reale non è praticamente fattibile con le risorse di un progetto piccolo.
- **Segnali multimodali oltre il testo**: incorpora dinamica di digitazione (velocità, ritmo, errori, latenza), non solo il contenuto testuale — la maggior parte degli strumenti di sentiment analysis lavora solo sul testo.
- **Rappresentazione a 8 dimensioni + PAD derivato**: cattura stati emotivi misti (es. "rabbia e tristezza insieme"), non solo positivo/negativo/neutro.

## Dove NOEMA è onestamente più debole

- **Accuratezza grezza di classificazione quasi certamente inferiore** a un modello transformer fine-tuned su un dataset ampio ed etichettato da umani. Un lessico di 488 parole, per quanto esteso, non si avvicina alla copertura implicita di un modello pre-addestrato su miliardi di parole.
- **Nessuna comprensione contestuale/semantica reale**: il sistema riconosce parole e pattern locali (negazione in una finestra di 3 token, intensificatori adiacenti), non il significato di una frase intera. Non riconosce sarcasmo, ironia, o dipendenze sintattiche complesse.
- **Copertura lessicale sempre incompleta**: 488 voci, per quanto ampliate con slang e parolacce, restano una frazione minima del vocabolario emotivo italiano reale. Un messaggio con vocabolario non incluso resta "neutro" — limite dichiarato fin dalla prima versione di questo progetto.
- **Mai validato su dati umani reali**: qualunque modello accademico o commerciale citato sopra è stato validato su benchmark con etichette umane. Questo sistema no — è il limite più importante, ripetuto in ogni versione di questo progetto perché resta vero.
- **Monolingua**: funziona solo in italiano, hard-coded. Le API commerciali sono tipicamente multilingua.

## In pratica: quale strumento per quale scopo

**Ha senso scegliere NOEMA (o un approccio simile) se**: serve trasparenza/auditabilità, i dati non devono lasciare il dispositivo, non si dispone di dati etichettati o GPU, serve personalizzazione rapida per singolo utente, o si vogliono incorporare segnali comportamentali oltre al testo. Casi d'uso ragionevoli: prototipi di ricerca, strumenti di auto-monitoraggio con consenso, dimostrazioni educative di AI interpretabile.

**NON ha senso scegliere NOEMA se**: serve la massima accuratezza possibile e la spiegabilità non è un requisito, si dispone già di dati etichettati e infrastruttura per fine-tuning, o l'uso è multilingua. In questi casi un modello transformer fine-tuned o un'API commerciale matura sono probabilmente la scelta migliore.

**NOEMA non è appropriato, in nessuna versione, per**: diagnosi cliniche, decisioni di assunzione/HR, qualunque processo decisionale automatizzato ad alto rischio su una persona. Nessuno strumento di questo tipo — commerciale o no — dovrebbe essere usato per questi scopi senza una validazione clinica/legale indipendente che va ben oltre la qualità del codice.
