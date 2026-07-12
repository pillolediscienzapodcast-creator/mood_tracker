# -*- coding: utf-8 -*-
"""
Test dimostrativo di NOEMA su dati sintetici (8 emozioni di base).

Simula una sequenza di turni conversazionali organizzati per emozione nota
e verifica che la traiettoria stimata dal modello si muova in modo
coerente, pur senza aver mai ricevuto un'etichetta esplicita durante
l'inferenza (le etichette qui sono usate solo per costruire lo scenario
e per il grafico finale, mai passate al modello).
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from noema import NoemaModel, EMOTIONS


def load_jsonl(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def run_demo():
    records = load_jsonl("training_data.jsonl")
    # Riordina per emozione (blocchi consecutivi) invece che mescolato, cosi'
    # il grafico mostra chiaramente le transizioni fra emozioni diverse.
    per_regime = {}
    for r in records:
        per_regime.setdefault(r["regime"], []).append(r)
    schedule = []
    for regime in EMOTIONS:
        schedule.extend(per_regime.get(regime, [])[:15])

    model = NoemaModel(seed=1)
    trace_intensities = []
    trace_regimi = []
    for rec in schedule:
        keydown_times = np.cumsum(rec.get("keydown_intervals", [])).tolist()
        from noema import text_features, keystroke_features, interaction_features, build_feature_vector
        tf = text_features(rec["text"])
        kf = keystroke_features(keydown_times, backspace_count=rec.get("backspace_count", 0))
        inf = interaction_features(rec.get("response_latency_s", 5.0), rec.get("is_followup", False),
                                    rec.get("followup_depth", 0), rec.get("hour_of_day", 12))
        u = build_feature_vector(tf, kf, inf)
        state = model.step(u)
        trace_intensities.append(state.intensities.copy())
        trace_regimi.append(rec["regime"])

    trace = np.array(trace_intensities)  # (n_turni, 8)

    print(f"{'regime':16s}" + "".join(f"{e[:5]:>7s}" for e in EMOTIONS))
    for regime in EMOTIONS:
        idx = [i for i, r in enumerate(trace_regimi) if r == regime]
        if not idx:
            continue
        medie = trace[idx].mean(axis=0)
        print(f"{regime:16s}" + "".join(f"{v:7.3f}" for v in medie))

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, emo in enumerate(EMOTIONS):
        ax.plot(trace[:, i], label=emo, linewidth=1.6)
    ax.axhline(0.5, color="black", linewidth=0.5, linestyle=":")
    ax.set_ylabel("intensita' stimata (0-1, 0.5=neutro)")
    ax.set_xlabel("turno")
    ax.set_title("NOEMA — traiettoria delle 8 emozioni di base su dati sintetici")
    ax.legend(loc="upper right", ncol=2, fontsize=9)

    boundaries = np.cumsum([len(per_regime.get(r, [])[:15]) for r in EMOTIONS])
    for b in boundaries[:-1]:
        ax.axvline(b, color="gray", linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig("noema_demo.png", dpi=140)
    print("\nGrafico salvato in noema_demo.png")


if __name__ == "__main__":
    run_demo()
