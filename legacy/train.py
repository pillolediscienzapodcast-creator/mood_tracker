# -*- coding: utf-8 -*-
"""
Pre-training iniziale di NOEMA su un dataset di turni (sintetico o reale).

IMPORTANTE: dopo il training esegue SEMPRE la batteria di controlli di
correttezza semantica (run_sanity_checks). Se il punteggio scende sotto
la soglia di sicurezza, il file dei parametri NON viene salvato di
default — meglio niente di nuovo che un modello peggiore di quello
vergine su casi ovvi (e' esattamente il tipo di errore trovato e corretto
in una versione precedente: vedi il documento teorico).

Uso:
    python3 train.py training_data.jsonl noema_params.json
"""
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from noema import NoemaModel, run_sanity_checks

SOGLIA_SICUREZZA_SANITY = 0.75  # sotto il 75% sui controlli di correttezza, non salvare


def load_jsonl(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def main():
    data_path = sys.argv[1] if len(sys.argv) > 1 else "training_data.jsonl"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "noema_params.json"
    forza_salvataggio = "--forza" in sys.argv

    records = load_jsonl(data_path)
    print(f"Caricati {len(records)} turni da {data_path}\n")

    model = NoemaModel(seed=1)

    B_before, C_before, K_before = model.B.copy(), model.C.copy(), model.K.copy()

    print("--- Controllo di correttezza semantica PRIMA del training ---")
    sanity_prima = run_sanity_checks(model, verbose=False)
    print(f"  {sanity_prima*100:.0f}% (modello vergine, solo prior)\n")

    model.fit(records, verbose=True)

    error_curve = [h["pred_error_norm"] for h in model.history]

    dB = float(np.linalg.norm(model.B - B_before))
    dC = float(np.linalg.norm(model.C - C_before))
    dK = float(np.linalg.norm(model.K - K_before))
    print(f"\nVariazione dei parametri dopo il training:")
    print(f"  |ΔB| = {dB:.4f}   |ΔC| = {dC:.4f}   |ΔK| = {dK:.4f}")

    first10 = float(np.mean(error_curve[:10]))
    last10 = float(np.mean(error_curve[-10:]))
    print(f"\nErrore di predizione medio — primi 10 turni: {first10:.4f} | ultimi 10 turni: {last10:.4f}")

    print("\n--- Controllo di correttezza semantica DOPO il training ---")
    sanity_dopo = run_sanity_checks(model, verbose=True)
    print(f"\n  Prima: {sanity_prima*100:.0f}%  ->  Dopo: {sanity_dopo*100:.0f}%")

    diagnostics = model.get_diagnostics()
    print(f"\nDiagnostica: baseline_saturato={diagnostics['baseline_saturato']}")

    if sanity_dopo < SOGLIA_SICUREZZA_SANITY and not forza_salvataggio:
        print(f"\n[ATTENZIONE] Il punteggio di correttezza semantica dopo il training "
              f"({sanity_dopo*100:.0f}%) e' sotto la soglia di sicurezza "
              f"({SOGLIA_SICUREZZA_SANITY*100:.0f}%).")
        print("Il file dei parametri NON e' stato salvato, per evitare di sostituire un "
              "modello vergine funzionante con uno che ha imparato associazioni sbagliate.")
        print("Rilancia con --forza per salvare comunque, oppure prova a modificare i dati "
              "di training o gli iperparametri.")
        return

    model.save_params(out_path)
    print(f"\nParametri salvati in: {out_path}")

    plt.figure(figsize=(9, 4))
    plt.plot(error_curve, alpha=0.35, label="errore per turno")
    window = 15
    if len(error_curve) >= window:
        smoothed = np.convolve(error_curve, np.ones(window) / window, mode="valid")
        plt.plot(range(window - 1, len(error_curve)), smoothed, linewidth=2,
                 label=f"media mobile ({window} turni)")
    plt.xlabel("turno di training")
    plt.ylabel("errore di predizione")
    plt.title("Curva di apprendimento di NOEMA durante il pre-training")
    plt.legend()
    plt.tight_layout()
    plt.savefig("training_curve.png", dpi=140)
    print("Curva di apprendimento salvata in training_curve.png")


if __name__ == "__main__":
    main()
