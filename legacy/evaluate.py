# -*- coding: utf-8 -*-
"""
Valuta se il pre-training migliora la capacita' del modello di prevedere
pattern comportamentali su dati mai visti, E che non abbia degradato la
correttezza semantica rispetto al modello vergine.

Uso:
    python3 evaluate.py noema_params.json test_data.jsonl
"""
import sys
import json
import numpy as np

from noema import NoemaModel, run_sanity_checks


def load_jsonl(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def average_error(model: NoemaModel, records: list) -> float:
    model.fit(records, verbose=False)
    errors = [h["pred_error_norm"] for h in model.history[-len(records):]]
    return float(np.mean(errors))


def main():
    params_path = sys.argv[1] if len(sys.argv) > 1 else "noema_params.json"
    test_path = sys.argv[2] if len(sys.argv) > 2 else "test_data.jsonl"

    test_records = load_jsonl(test_path)
    print(f"Turni di test (mai visti durante il training): {len(test_records)}\n")

    baseline = NoemaModel(seed=1)
    err_baseline = average_error(baseline, test_records)
    sanity_baseline = run_sanity_checks(NoemaModel(seed=1), verbose=False)

    trained = NoemaModel(seed=1)
    trained.load_params(params_path)
    trained.reset_state()
    err_trained = average_error(trained, test_records)
    sanity_trained = run_sanity_checks(trained, verbose=False)

    print("Errore medio di predizione su dati mai visti prima:")
    print(f"  modello NON allenato (solo prior):  {err_baseline:.4f}  (sanity check: {sanity_baseline*100:.0f}%)")
    print(f"  modello PRE-ALLENATO:                {err_trained:.4f}  (sanity check: {sanity_trained*100:.0f}%)")

    improvement = 100 * (err_baseline - err_trained) / err_baseline
    print(f"\nMiglioramento predizione: {improvement:+.1f}%")

    if sanity_trained < sanity_baseline:
        print(f"\n[ATTENZIONE] Il training ha PEGGIORATO la correttezza semantica "
              f"({sanity_baseline*100:.0f}% -> {sanity_trained*100:.0f}%). "
              f"Il miglioramento nella metrica di predizione non garantisce, da solo, "
              f"un modello migliore in senso utile — vedi il documento teorico.")
    else:
        print(f"\nLa correttezza semantica non e' peggiorata "
              f"({sanity_baseline*100:.0f}% -> {sanity_trained*100:.0f}%): "
              f"il miglioramento nella predizione e' un progresso reale, non un artefatto.")


if __name__ == "__main__":
    main()
