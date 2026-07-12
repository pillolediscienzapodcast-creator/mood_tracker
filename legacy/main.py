# -*- coding: utf-8 -*-
"""
NOEMA — Applicazione interattiva da riga di comando
======================================================

Avvia il demone, lascia scrivere messaggi liberamente catturando i tempi
di digitazione reali (solo di QUESTA sessione, non un keylogger globale:
cattura esclusivamente cio' che viene digitato in questo prompt), mostra
la stima dello stato emotivo, e permette di dare un feedback
(giusto/sbagliato) che il modello usa per correggersi e migliorare nel
tempo su quella specifica persona.

USO RESPONSABILE: esegui questo programma solo su te stesso, o su una
persona che ha dato consenso esplicito e informato ad essere monitorata.
Non e' uno strumento diagnostico. Leggi il documento teorico incluso
prima di un uso reale.

Uso:
    python3 main.py
    python3 main.py --profilo mario
"""
import sys
import os
import time
import json
import argparse

from noema import NoemaDaemon, NoemaModel, EMOTIONS


# =============================================================================
# Cattura dei tempi di digitazione (solo di questa sessione, nessuna
# libreria esterna necessaria)
# =============================================================================

def leggi_riga_con_tempi():
    """
    Legge una riga di input catturando il timestamp di ogni tasto premuto
    IN QUESTO PROMPT (non un keylogger globale: non vede nulla al di fuori
    di questa riga di input). Funziona su Windows (msvcrt) e Unix/macOS
    (termios/tty); se nessuno dei due e' disponibile (es. terminale non
    interattivo, IDE particolari), usa un fallback senza tempi precisi.

    Ritorna: (testo, lista_timestamp_assoluti, n_backspace)
    """
    testo = []
    tempi = []
    n_backspace = 0

    # --- Windows ---
    try:
        import msvcrt
        while True:
            ch = msvcrt.getwch()
            t = time.time()
            if ch in ("\r", "\n"):
                print()
                break
            elif ch == "\x08":
                n_backspace += 1
                if testo:
                    testo.pop()
                    if tempi:
                        tempi.pop()
                sys.stdout.write("\b \b")
                sys.stdout.flush()
            elif ch == "\x03":
                raise KeyboardInterrupt
            else:
                testo.append(ch)
                tempi.append(t)
                sys.stdout.write(ch)
                sys.stdout.flush()
        return "".join(testo), tempi, n_backspace
    except ImportError:
        pass  # non siamo su Windows, proviamo termios

    # --- Unix / macOS ---
    try:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                t = time.time()
                if ch in ("\r", "\n"):
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    break
                elif ch in ("\x7f", "\x08"):
                    n_backspace += 1
                    if testo:
                        testo.pop()
                        if tempi:
                            tempi.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                elif ch == "\x03":
                    raise KeyboardInterrupt
                else:
                    testo.append(ch)
                    tempi.append(t)
                    sys.stdout.write(ch)
                    sys.stdout.flush()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return "".join(testo), tempi, n_backspace
    except Exception:
        pass  # terminale non interattivo o piattaforma non supportata

    # --- Fallback: input normale, senza tempi di digitazione precisi ---
    testo_str = input()
    ora = time.time()
    tempi = [ora + i * 0.15 for i in range(len(testo_str))]
    print("[NOEMA] (Tempi di digitazione stimati: cattura precisa non disponibile "
          "in questo terminale.)")
    return testo_str, tempi, 0


# =============================================================================
# Utility di interfaccia
# =============================================================================

def stampa_intestazione():
    print("=" * 70)
    print("  NOEMA — tracciamento sperimentale dello stato emotivo")
    print("=" * 70)
    print(
        "Prototipo di ricerca, non uno strumento diagnostico. Le stime sono\n"
        "inferenze automatiche da proxy comportamentali (testo, tempi di\n"
        "digitazione), non letture certe del tuo stato reale.\n"
        "Usalo solo su te stesso o con il consenso esplicito della persona\n"
        "monitorata. Scrivi 'exit' per uscire, 'diagnostica' per lo stato\n"
        "interno del modello, 'aiuto' per i comandi disponibili.\n"
    )
    print("-" * 70)


def stampa_stato(record: dict):
    print()
    print(f"  Valenza={record['valence']:+.2f}  Arousal={record['arousal']:+.2f}  "
          f"Dominanza={record['dominance']:+.2f}  Confidenza={record['confidence_proxy']:.2f}")
    print(f"  {record['label']}")
    print()


def chiedi_feedback(daemon: NoemaDaemon):
    risposta = input("  E' corretto? [s = si' / n = no / invio = salta] > ").strip().lower()
    if risposta == "s":
        daemon.provide_feedback(corretto=True)
    elif risposta == "n":
        print("  Quale emozione descrive meglio lo stato reale?")
        for i, e in enumerate(EMOTIONS, 1):
            print(f"    {i}. {e}")
        scelta = input("  Numero (invio per annullare) > ").strip()
        if scelta.isdigit() and 1 <= int(scelta) <= len(EMOTIONS):
            emozione = EMOTIONS[int(scelta) - 1]
            daemon.provide_feedback(corretto=False, emozione_corretta=emozione)
        else:
            print("  Annullato, nessun feedback registrato.")
    # invio vuoto -> salta, nessuna azione


def calibrazione_opzionale(daemon: NoemaDaemon):
    print(
        "\nPuoi (facoltativamente) fornire un testo scritto DA TE STESSO — una\n"
        "bio, un post, un articolo — per calibrare il modello sul tuo modo di\n"
        "scrivere prima di iniziare. NON incollare testo scritto da altre\n"
        "persone o preso da profili social/LinkedIn altrui: questo strumento\n"
        "e' pensato per l'auto-calibrazione con consenso, non per profilare\n"
        "terzi a partire da contenuti pubblici.\n"
    )
    vuoi = input("Vuoi fornire un testo di calibrazione? [s/n] > ").strip().lower()
    if vuoi != "s":
        return
    percorso = input("Percorso del file di testo (invio per incollare direttamente) > ").strip()
    if percorso:
        try:
            with open(percorso, encoding="utf-8") as f:
                testo = f.read()
        except OSError as e:
            print(f"  Impossibile leggere il file: {e}")
            return
    else:
        print("  Incolla il testo, poi una riga vuota per terminare:")
        righe = []
        while True:
            riga = input()
            if riga == "":
                break
            righe.append(riga)
        testo = "\n".join(righe)
    if testo.strip():
        daemon.calibra_con_testo(testo)


def stampa_diagnostica(daemon: NoemaDaemon):
    diag = daemon.model.get_diagnostics()
    print("\n--- Diagnostica del modello ---")
    for k, v in diag.items():
        print(f"  {k}: {v}")
    print()


def stampa_aiuto():
    print(
        "\nComandi disponibili:\n"
        "  exit          esce e salva il profilo\n"
        "  diagnostica   mostra lo stato interno del modello\n"
        "  aiuto         mostra questo messaggio\n"
        "  (qualsiasi altro testo viene trattato come messaggio da analizzare)\n"
    )


# =============================================================================
# Ciclo principale
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="NOEMA — applicazione interattiva")
    parser.add_argument("--profilo", default="default",
                         help="Nome del profilo utente (parametri salvati separatamente per profilo)")
    parser.add_argument("--reset", action="store_true",
                         help="Ignora un profilo salvato esistente e riparte da zero")
    args = parser.parse_args()

    os.makedirs("profili", exist_ok=True)
    params_path = os.path.join("profili", f"{args.profilo}.json")
    log_path = os.path.join("profili", f"{args.profilo}_log.jsonl")

    stampa_intestazione()

    if os.path.exists(params_path) and not args.reset:
        print(f"Profilo '{args.profilo}' trovato, carico i parametri salvati...")
        daemon = NoemaDaemon(params_path=params_path, log_path=log_path)
        diag = daemon.model.get_diagnostics()
        print(f"  (turni processati finora: {diag['turni_processati']}, "
              f"feedback ricevuti: {diag['feedback_ricevuti']})\n")
    elif os.path.exists("noema_params.json"):
        print(f"Nuovo profilo '{args.profilo}': parto dal modello pre-allenato "
              f"'noema_params.json' invece che da zero (consigliato: un modello mai "
              f"allenato ha confidenza strutturalmente bassa e riconosce molto meno).")
        daemon = NoemaDaemon(params_path="noema_params.json", log_path=log_path)
        calibrazione_opzionale(daemon)
        print()
    else:
        print(f"Nuovo profilo '{args.profilo}' (nessun modello pre-allenato trovato: "
              f"parto da zero — la confidenza sara' bassa finche' non impari abbastanza).")
        daemon = NoemaDaemon(model=NoemaModel(), log_path=log_path)
        calibrazione_opzionale(daemon)
        print()

    turno = 0
    try:
        while True:
            print(f"[{turno+1}] Scrivi un messaggio > ", end="", flush=True)
            t_latenza_inizio = time.time()
            testo, tempi, n_backspace = leggi_riga_con_tempi()
            latenza = time.time() - t_latenza_inizio

            comando = testo.strip().lower()
            if comando == "exit":
                break
            elif comando == "diagnostica":
                stampa_diagnostica(daemon)
                continue
            elif comando == "aiuto":
                stampa_aiuto()
                continue
            elif not testo.strip():
                continue

            record = daemon.ingest_turn(
                text=testo,
                keydown_times=tempi,
                backspace_count=n_backspace,
                response_latency_s=latenza,
                is_followup=(turno > 0),
                followup_depth=min(turno, 5),
            )
            stampa_stato(record)
            chiedi_feedback(daemon)
            turno += 1

            if (turno % 10) == 0:
                daemon.model.save_params(params_path)
                print(f"  [NOEMA] Salvataggio automatico del profilo ({turno} turni).\n")

    except KeyboardInterrupt:
        print("\n\nInterrotto dall'utente.")

    daemon.model.save_params(params_path)
    diag = daemon.model.get_diagnostics()
    print("\n" + "-" * 70)
    print(f"Sessione terminata. Profilo '{args.profilo}' salvato in {params_path}.")
    print(f"Turni totali processati: {diag['turni_processati']}  |  "
          f"Feedback ricevuti: {diag['feedback_ricevuti']}")
    print("-" * 70)


if __name__ == "__main__":
    main()
