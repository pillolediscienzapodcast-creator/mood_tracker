# -*- coding: utf-8 -*-
"""
Suite di test automatici per NOEMA.

Uso:
    pip install pytest
    pytest test_noema.py -v

Copre: estrazione feature testuali (incluse negazione, intensificatori
bidirezionali, censura/leet/ripetizioni), dinamica di digitazione,
nucleo adattivo (evoluzione dello stato, RLS, feedback supervisionato,
persistenza), robustezza a input anomali, stabilita' numerica su sessioni
lunghe, e la batteria di controlli di correttezza semantica come vero e
proprio test automatico (non solo uno script da eseguire a mano).

Questo file esiste per rendere verificabili in modo ripetibile le
proprieta' che finora erano state controllate manualmente durante lo
sviluppo — ogni bug trovato e corretto (vedi NOEMA_documentazione.md,
§5-5quinquies) ha un test dedicato che ne impedisce il ripresentarsi
inosservato.
"""
import math
import numpy as np
import pytest

from noema import (
    NoemaModel, NoemaDaemon, EmotionalState, EMOTIONS, N_FEATURES,
    text_features, keystroke_features, interaction_features,
    build_feature_vector, run_sanity_checks, _trova_nel_lessico,
)


# =============================================================================
# 1. Estrazione feature testuali
# =============================================================================

class TestTextFeatures:
    def test_parola_riconosciuta_esatta(self):
        f = text_features("sono molto felice")
        assert f["lex_gioia"] > 0

    def test_parola_non_riconosciuta_non_esplode(self):
        f = text_features("xyzabc qwerty asdfgh")
        assert all(f[f"lex_{e}"] == 0 for e in EMOTIONS)

    def test_testo_vuoto_non_esplode(self):
        f = text_features("")
        assert all(math.isfinite(v) for v in f.values())

    def test_negazione_attenua_o_inverte(self):
        f_pos = text_features("sono felice")
        f_neg = text_features("non sono felice")
        assert f_neg["lex_gioia"] < f_pos["lex_gioia"]

    def test_negazione_finale_non_collegata_non_scatta(self):
        f = text_features("sono felice, non e' vero?")
        assert f["lex_gioia"] > 0

    def test_intensificatore_prima(self):
        f_base = text_features("sono felice")
        f_int = text_features("sono molto felice")
        assert f_int["lex_gioia"] > f_base["lex_gioia"]

    def test_intensificatore_dopo(self):
        f_base = text_features("mi piace questa cosa")
        f_int = text_features("mi piace tantissimo questa cosa")
        assert f_int["lex_gioia"] > f_base["lex_gioia"]

    def test_superlativo(self):
        f_base = text_features("sono triste")
        f_sup = text_features("sono tristissimo")
        assert f_sup["lex_tristezza"] > f_base["lex_tristezza"]

    @pytest.mark.parametrize("testo,emo_attesa", [
        ("che gioia incredibile", "gioia"),
        ("sono molto arrabbiato", "rabbia"),
        ("ho una paura tremenda", "paura"),
    ])
    def test_lessico_di_base(self, testo, emo_attesa):
        f = text_features(testo)
        assert f[f"lex_{emo_attesa}"] > 0

    def test_emozioni_di_base_sono_parole_del_lessico(self):
        for emo in EMOTIONS:
            f = text_features(f"sento molta {emo}")
            assert f[f"lex_{emo}"] > 0, f"'{emo}' non e' riconosciuta come parola del lessico"


class TestNormalizzazioneScrittura:
    """Copre il riconoscimento di parole scritte in modo non standard
    (slang, censura, leet, lettere ripetute)."""

    def test_lettere_ripetute(self):
        assert _trova_nel_lessico("grazieee") is not None
        assert _trova_nel_lessico("grazieee") == _trova_nel_lessico("grazie")

    def test_leet_numeri(self):
        assert _trova_nel_lessico("felic1ssimo") is not None
        assert _trova_nel_lessico("c4zzo") is not None

    def test_k_al_posto_di_c(self):
        assert _trova_nel_lessico("kazzo") is not None

    def test_censura_asterischi_univoca(self):
        risultato = _trova_nel_lessico("ca**o")
        assert risultato is not None
        assert risultato == _trova_nel_lessico("cazzo")

    def test_censura_ambigua_non_esplode(self):
        risultato = _trova_nel_lessico("**zzo")
        assert risultato is None or isinstance(risultato, dict)

    def test_parola_normale_non_alterata_da_normalizzazione(self):
        assert _trova_nel_lessico("felice") == {"gioia": 0.8}

    def test_stemming_riconosce_coniugazioni_verbali(self):
        # "arrabbiato" e' nel lessico; le sue coniugazioni non elencate
        # esplicitamente devono comunque essere riconosciute via radice.
        assert _trova_nel_lessico("arrabbiava") is not None
        assert _trova_nel_lessico("arrabbiarsi") is not None

    def test_stemming_non_riconosce_parole_neutre(self):
        assert _trova_nel_lessico("gatto") is None
        assert _trova_nel_lessico("tavolo") is None

    def test_frase_idiomatica_non_vedo_lora(self):
        # "non vedo l'ora" non e' una negazione: e' attesa positiva. Deve
        # essere riconosciuta come frase PRIMA che "non" venga trattato
        # come negatore della parola successiva.
        f = text_features("non vedo l'ora di iniziare")
        assert f["lex_anticipazione"] > 0
        assert f["lex_gioia"] >= 0  # non deve risultare negativo per errore

    def test_frase_idiomatica_che_due_palle(self):
        f = text_features("che due palle oggi")
        assert f["lex_rabbia"] > 0


# =============================================================================
# 2. Dinamica di digitazione e interazione
# =============================================================================

class TestKeystrokeFeatures:
    def test_pochi_tasti_non_esplode(self):
        f = keystroke_features([0.1])
        assert all(math.isfinite(v) for v in f.values())

    def test_nessun_tasto_non_esplode(self):
        f = keystroke_features([])
        assert all(math.isfinite(v) for v in f.values())

    def test_digitazione_veloce_vs_lenta(self):
        veloce = keystroke_features(list(np.cumsum([0.05] * 10)))
        lenta = keystroke_features(list(np.cumsum([0.5] * 10)))
        assert veloce["typing_speed"] > lenta["typing_speed"]

    def test_baseline_personale_relativa(self):
        base = {"typing_speed_mean": 5.0, "typing_speed_std": 1.0}
        f = keystroke_features(list(np.cumsum([0.1] * 10)), personal_baseline=base)
        assert -4 <= f["typing_speed_relative"] <= 4


class TestBuildFeatureVector:
    def test_dimensione_corretta(self):
        u = build_feature_vector(text_features("ciao"), keystroke_features([0.1, 0.2]),
                                  interaction_features(3.0, False, 0, 12))
        assert u.shape == (N_FEATURES,)

    def test_valori_finiti_e_limitati(self):
        u = build_feature_vector(text_features("ciao"), keystroke_features([0.1, 0.2]),
                                  interaction_features(3.0, False, 0, 12))
        assert np.all(np.isfinite(u))
        assert np.all(np.abs(u) <= 4.0)

    def test_input_anomalo_non_esplode(self):
        u = build_feature_vector(
            text_features("a" * 500),
            keystroke_features(list(np.cumsum([0.001] * 200)), backspace_count=500),
            interaction_features(999999.0, True, 999, 12),
        )
        assert np.all(np.isfinite(u))
        assert np.all(np.abs(u) <= 4.0)


# =============================================================================
# 3. Nucleo adattivo — stato, dinamica, persistenza
# =============================================================================

class TestEmotionalState:
    def test_stato_neutro_intensita_a_meta(self):
        s = EmotionalState()
        assert np.allclose(s.intensities, 0.5, atol=1e-6)

    def test_pad_neutro_a_zero(self):
        s = EmotionalState()
        assert np.allclose(s.pad, 0.0, atol=1e-6)

    def test_dominanti_vuoto_se_tutto_neutro(self):
        s = EmotionalState()
        assert s.dominanti() == []


class TestNoemaModelStep:
    def test_step_produce_stato_valido(self):
        m = NoemaModel(seed=0)
        u = build_feature_vector(text_features("sono felice"), keystroke_features([0.1, 0.2]),
                                  interaction_features(3.0, False, 0, 12))
        state = m.step(u)
        assert np.all(np.isfinite(state.z))
        assert np.all((state.intensities >= 0) & (state.intensities <= 1))

    def test_update_false_non_modifica_parametri(self):
        m = NoemaModel(seed=0)
        B_prima = m.B.copy()
        u = build_feature_vector(text_features("sono felice"), keystroke_features([0.1, 0.2]),
                                  interaction_features(3.0, False, 0, 12))
        m.step(u, update=False)
        assert np.allclose(m.B, B_prima)

    def test_update_true_modifica_parametri(self):
        m = NoemaModel(seed=0)
        B_prima = m.B.copy()
        u = build_feature_vector(text_features("sono felice"), keystroke_features([0.1, 0.2]),
                                  interaction_features(3.0, False, 0, 12))
        m.step(u, update=True)
        assert not np.allclose(m.B, B_prima)

    def test_testo_positivo_alza_gioia_rispetto_al_neutro(self):
        m = NoemaModel(seed=0)
        u_neutro = build_feature_vector(text_features("ciao"), keystroke_features([0.15, 0.3]),
                                         interaction_features(4.0, False, 0, 12))
        u_felice = build_feature_vector(text_features("sono molto felice"), keystroke_features([0.15, 0.3]),
                                         interaction_features(4.0, False, 0, 12))
        # step() ritorna un riferimento a self.state (oggetto mutabile
        # persistente, non una nuova istanza ad ogni chiamata): va copiata
        # l'intensita' subito dopo ciascuna chiamata, altrimenti la
        # seconda chiamata sovrascriverebbe silenziosamente anche il
        # valore letto per la prima.
        gioia_neutro = m.step(u_neutro, update=False).intensities[EMOTIONS.index("gioia")].copy()
        m.reset_state()
        gioia_felice = m.step(u_felice, update=False).intensities[EMOTIONS.index("gioia")].copy()
        assert gioia_felice > gioia_neutro


class TestPersistenza:
    def test_save_load_roundtrip(self, tmp_path):
        m1 = NoemaModel(seed=0)
        u = build_feature_vector(text_features("sono felice"), keystroke_features([0.1, 0.2]),
                                  interaction_features(3.0, False, 0, 12))
        m1.step(u)
        path = str(tmp_path / "params.json")
        m1.save_params(path)

        m2 = NoemaModel(seed=99)
        m2.load_params(path)
        assert np.allclose(m1.B, m2.B)
        assert np.allclose(m1.z0, m2.z0)
        assert np.allclose(m1.state.z, m2.state.z)

    def test_reset_state_mantiene_parametri(self, tmp_path):
        m = NoemaModel(seed=0)
        u = build_feature_vector(text_features("sono molto arrabbiato"), keystroke_features([0.05, 0.1]),
                                  interaction_features(1.0, False, 0, 12))
        m.step(u)
        B_dopo_training = m.B.copy()
        m.reset_state()
        assert np.allclose(m.state.z, m.z0)
        assert np.allclose(m.B, B_dopo_training)

    def test_load_file_inesistente_solleva_errore(self):
        m = NoemaModel(seed=0)
        with pytest.raises(OSError):
            m.load_params("/percorso/che/non/esiste.json")


# =============================================================================
# 4. Feedback supervisionato
# =============================================================================

class TestFeedback:
    def test_feedback_senza_turno_precedente_solleva_errore(self):
        m = NoemaModel(seed=0)
        with pytest.raises(RuntimeError):
            m.apply_feedback(corretto=True)

    def test_feedback_emozione_invalida_solleva_errore(self):
        m = NoemaModel(seed=0)
        u = build_feature_vector(text_features("ciao"), keystroke_features([0.1, 0.2]),
                                  interaction_features(3.0, False, 0, 12))
        m.step(u)
        with pytest.raises(ValueError):
            m.apply_feedback(corretto=False, emozione_corretta="emozione_inventata")

    def test_consolidamento_automatico_dopo_n_feedback(self):
        m = NoemaModel(seed=0, consolidation_every=3)
        for i in range(3):
            u = build_feature_vector(text_features("sono felice"), keystroke_features([0.1, 0.2]),
                                      interaction_features(3.0, False, 0, 12))
            m.step(u)
            m.apply_feedback(corretto=True)
        assert len(m._feedback_buffer) == 0
        assert m._feedback_count == 3

    def test_feedback_corretto_sposta_stato_verso_target(self):
        m = NoemaModel(seed=0)
        u = build_feature_vector(text_features("ciao"), keystroke_features([0.1, 0.2]),
                                  interaction_features(3.0, False, 0, 12))
        m.step(u)
        z_prima = m.state.z.copy()
        m.apply_feedback(corretto=False, emozione_corretta="rabbia", intensita=0.9)
        idx = EMOTIONS.index("rabbia")
        assert m.state.z[idx] > z_prima[idx]


# =============================================================================
# 5. Demone — integrazione end-to-end
# =============================================================================

class TestNoemaDaemon:
    def test_ingest_turn_schema_output(self):
        d = NoemaDaemon()
        r = d.ingest_turn(text="sono felice", keydown_times=[0.1, 0.2, 0.3],
                           backspace_count=0, response_latency_s=3.0,
                           is_followup=False, followup_depth=0)
        for campo in ("timestamp", "valence", "arousal", "dominance", "emozioni",
                      "emozioni_dominanti", "confidence_proxy", "label"):
            assert campo in r
        assert isinstance(r["label"], str) and len(r["label"]) > 0
        assert 0.0 <= r["confidence_proxy"] <= 1.0
        assert -1.0 <= r["valence"] <= 1.0

    def test_nota_trasparenza_quando_nessuna_parola_riconosciuta(self):
        d = NoemaDaemon()
        r = d.ingest_turn(text="xyzabc qwerty", keydown_times=[0.1, 0.2],
                           backspace_count=0, response_latency_s=3.0,
                           is_followup=False, followup_depth=0)
        assert "nessuna parola" in r["label"].lower()

    def test_reset_state_on_load_di_default(self, tmp_path):
        m = NoemaModel(seed=0)
        u = build_feature_vector(text_features("sono molto arrabbiato"), keystroke_features([0.05, 0.1]),
                                  interaction_features(1.0, False, 0, 12))
        m.step(u)
        path = str(tmp_path / "params.json")
        m.save_params(path)

        d = NoemaDaemon(params_path=path)
        assert np.allclose(d.model.state.z, d.model.z0)

    def test_reset_state_on_load_disattivabile(self, tmp_path):
        m = NoemaModel(seed=0)
        u = build_feature_vector(text_features("sono molto arrabbiato"), keystroke_features([0.05, 0.1]),
                                  interaction_features(1.0, False, 0, 12))
        m.step(u)
        z_salvato = m.state.z.copy()
        path = str(tmp_path / "params.json")
        m.save_params(path)

        d = NoemaDaemon(params_path=path, reset_state_on_load=False)
        assert np.allclose(d.model.state.z, z_salvato)


# =============================================================================
# 6. Stabilita' numerica su sessioni lunghe
# =============================================================================

class TestStabilitaNumerica:
    def test_nessun_nan_dopo_500_turni_misti(self):
        m = NoemaModel(seed=0)
        rng = np.random.default_rng(0)
        testi = ["sono felice", "che tristezza", "sono arrabbiato", "che paura",
                 "wow che sorpresa", "che schifo", "non vedo l'ora", "mi fido di te",
                 "ciao", "xyzabc"]
        for i in range(500):
            testo = testi[i % len(testi)]
            n = max(2, len(testo.replace(" ", "")))
            tempi = list(np.cumsum(rng.uniform(0.05, 0.3, size=n)))
            u = build_feature_vector(text_features(testo), keystroke_features(tempi, backspace_count=i % 5),
                                      interaction_features(float(rng.uniform(1, 10)), i % 2 == 0, i % 3, i % 24))
            m.step(u)
        assert np.all(np.isfinite(m.state.z))
        assert np.all(np.isfinite(m.B))
        assert np.all(np.isfinite(m.C))
        assert np.all(np.isfinite(m.z0))

    def test_nessun_asse_saturo_dopo_500_turni_misti(self):
        m = NoemaModel(seed=0)
        rng = np.random.default_rng(1)
        testi = ["sono felice", "che tristezza", "sono arrabbiato", "che paura",
                 "wow che sorpresa", "che schifo", "non vedo l'ora", "mi fido di te"]
        for i in range(500):
            testo = testi[i % len(testi)]
            n = max(2, len(testo.replace(" ", "")))
            tempi = list(np.cumsum(rng.uniform(0.05, 0.3, size=n)))
            u = build_feature_vector(text_features(testo), keystroke_features(tempi),
                                      interaction_features(float(rng.uniform(1, 10)), False, 0, i % 24))
            m.step(u)
        diag = m.get_diagnostics()
        assert not diag["baseline_saturato"]


# =============================================================================
# 7. Controllo di correttezza semantica come test automatico
# =============================================================================

class TestCorrettezzaSemantica:
    SOGLIA_MINIMA = 0.75

    def test_modello_vergine_supera_la_soglia(self):
        m = NoemaModel(seed=1)
        frazione = run_sanity_checks(m, verbose=False)
        assert frazione >= self.SOGLIA_MINIMA

    def test_modello_preallenato_supera_la_soglia(self):
        m = NoemaModel(seed=1)
        try:
            m.load_params("noema_params.json")
        except OSError:
            pytest.skip("noema_params.json non presente in questa cartella")
        frazione = run_sanity_checks(m, verbose=False)
        assert frazione >= self.SOGLIA_MINIMA


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
