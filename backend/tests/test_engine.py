"""Test del motore NOEMA (puri, senza database)."""

import numpy as np

from app.engine import model as engine_model
from app.engine.emotions import EMOTIONS
from app.engine.features import (
    N_FEATURES,
    build_feature_vector,
    interaction_features,
    keystroke_features,
    text_features,
)
from app.engine.feedback import apply_feedback
from app.engine.params import ModelParams, init_params
from app.engine.pretrained import load_pretrained
from app.engine.sanity import run_sanity_checks


def _u(text: str) -> np.ndarray:
    tf = text_features(text)
    kf = keystroke_features([0.18, 0.35, 0.52, 0.71, 0.90])
    inf = interaction_features(5.0, False, 0, 12)
    return build_feature_vector(tf, kf, inf)


class TestFeatures:
    def test_vettore_ha_dimensione_attesa(self):
        assert _u("sono felice").shape == (N_FEATURES,)

    def test_parola_nel_lessico_riconosciuta(self):
        assert text_features("sono felicissimo")["lex_gioia"] > 0

    def test_negazione_attenua(self):
        pos = text_features("sono felice")["lex_gioia"]
        neg = text_features("non sono felice")["lex_gioia"]
        assert neg < pos

    def test_intensificatore_amplifica(self):
        base = text_features("sono felice")["lex_gioia"]
        amp = text_features("sono molto felice")["lex_gioia"]
        assert amp > base

    def test_emoji_riconosciuta(self):
        assert text_features("che giornata 😢")["lex_tristezza"] > 0

    def test_input_anomalo_non_esplode(self):
        v = build_feature_vector(
            text_features(""),
            keystroke_features([]),
            interaction_features(0, False, 0, 0),
        )
        assert np.all(np.isfinite(v))


class TestModel:
    def test_sanity_vergine_sopra_soglia(self):
        assert run_sanity_checks(init_params(seed=1)) >= 0.75

    def test_sanity_pretrained_sopra_soglia(self):
        assert run_sanity_checks(load_pretrained()) >= 0.75

    def test_serializzazione_round_trip(self):
        p = init_params(seed=3)
        engine_model.step(p, _u("sono triste"))
        p2 = ModelParams.from_dict(p.to_dict())
        assert np.allclose(p.B, p2.B) and np.allclose(p.z, p2.z)
        assert p.t == p2.t

    def test_stabilita_su_molti_turni(self):
        p = init_params(seed=1)
        for _ in range(200):
            engine_model.step(p, _u("oggi va tutto bene"))
        assert np.all(np.isfinite(p.z)) and np.all(np.isfinite(p.B))

    def test_emozione_dominante_chiara(self):
        p = load_pretrained()
        engine_model.reset_state(p)
        r = engine_model.step(p, _u("sono arrabbiato e furioso, odio tutto"))
        assert r.dominant and r.dominant[0][0] == "rabbia"


class TestFeedback:
    def test_feedback_sposta_stato_verso_emozione(self):
        p = init_params(seed=1)
        engine_model.step(p, _u("ciao"))
        prima = engine_model.emotions.intensities(p.z, p.alpha)[
            EMOTIONS.index("tristezza")
        ]
        apply_feedback(p, corretto=False, emozione_corretta="tristezza")
        dopo = engine_model.emotions.intensities(p.z, p.alpha)[
            EMOTIONS.index("tristezza")
        ]
        assert dopo > prima
        assert p.feedback_count == 1
