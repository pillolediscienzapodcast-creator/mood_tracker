"""Servizi del dominio NOEMA: orchestrano il motore e i repository.

Confine di transazione: ogni operazione carica lo stato del modello con
lock, chiama il motore puro, persiste turno/feedback e risalva i parametri
aggiornati NELLA STESSA transazione. Il commit e' responsabilita' del
chiamante (la route) tramite la Session iniettata.
"""

from __future__ import annotations

import datetime

import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.engine import feedback as engine_feedback
from app.engine import model as engine_model
from app.engine.emotions import EMOTIONS
from app.engine.features import (
    build_feature_vector,
    interaction_features,
    keystroke_features,
    text_features,
)
from app.engine.labels import genera_descrizione
from app.engine.params import ModelParams
from app.engine.pretrained import load_pretrained
from app.models.mood import EmotionalModelState, EmotionalTurn
from app.repositories.feedback import FeedbackRepository
from app.repositories.model_state import ModelStateRepository
from app.repositories.turn import TurnRepository

# In uso live l'apprendimento auto-supervisionato e' attenuato: testo reale
# fuori distribuzione puo' generare correzioni sproporzionate e drift. La
# personalizzazione affidabile e' delegata al feedback umano esplicito.
LIVE_LEARN_RATE = 0.15


class MoodService:
    def __init__(self, db: Session):
        self.db = db
        self.states = ModelStateRepository(db)
        self.turns = TurnRepository(db)
        self.feedback = FeedbackRepository(db)

    # ------------------------------------------------------------------
    # Stato del modello
    # ------------------------------------------------------------------
    def _ensure_state(self, user_id: int) -> EmotionalModelState:
        """Carica lo stato con lock, creandolo dai parametri pre-allenati
        al primo accesso."""
        state = self.states.get_for_update(user_id)
        if state is None:
            params = load_pretrained()
            engine_model.reset_state(params)  # parte dal baseline appreso
            state = self.states.create(
                user_id=user_id,
                params=params.to_dict(),
                model_version=params.model_version,
                n_turns_trained=params.t,
                feedback_count=params.feedback_count,
            )
        return state

    # ------------------------------------------------------------------
    # Ingest di un turno
    # ------------------------------------------------------------------
    def ingest_turn(
        self,
        user_id: int,
        *,
        text: str,
        keydown_times: list[float],
        backspace_count: int,
        response_latency_s: float,
        is_followup: bool,
        followup_depth: int,
        hour_of_day: int | None = None,
    ) -> EmotionalTurn:
        state = self._ensure_state(user_id)
        params = ModelParams.from_dict(state.params)

        if hour_of_day is None:
            hour_of_day = datetime.datetime.now().hour

        tf = text_features(text)
        kf = keystroke_features(
            keydown_times,
            backspace_count=backspace_count,
            personal_baseline=params.personal_typing_baseline(),
        )
        inf = interaction_features(
            response_latency_s, is_followup, followup_depth, hour_of_day
        )
        u = build_feature_vector(tf, kf, inf)

        result = engine_model.step(
            params, u, update=True, learn_rate_scale=LIVE_LEARN_RATE
        )
        no_lexicon_match = all(tf.get(f"lex_{e}", 0.0) == 0.0 for e in EMOTIONS)
        label = genera_descrizione(
            result.dominant,
            result.pad,
            result.confidence,
            nessuna_parola_riconosciuta=no_lexicon_match,
        )

        turn = self.turns.create(
            user_id=user_id,
            text=text if settings.store_turn_text else None,
            response_latency_s=response_latency_s,
            backspace_count=backspace_count,
            is_followup=is_followup,
            followup_depth=followup_depth,
            hour_of_day=hour_of_day,
            feature_vector=[float(x) for x in u],
            emotions={
                e: round(float(x), 4) for e, x in zip(EMOTIONS, result.intensities)
            },
            dominant_emotions=[[n, round(i, 4)] for n, i in result.dominant],
            valence=float(result.pad[0]),
            arousal=float(result.pad[1]),
            dominance=float(result.pad[2]),
            confidence=result.confidence,
            label=label,
            no_lexicon_match=no_lexicon_match,
        )
        self.states.update_params(
            state,
            params.to_dict(),
            n_turns_trained=params.t,
            feedback_count=params.feedback_count,
        )
        return turn

    # ------------------------------------------------------------------
    # Feedback + consolidamento
    # ------------------------------------------------------------------
    def apply_feedback(
        self,
        user_id: int,
        turn_id: int,
        *,
        corretto: bool,
        emozione_corretta: str | None,
    ) -> dict:
        turn = self.turns.get(turn_id)
        if turn is None or turn.user_id != user_id:
            raise LookupError("turn_not_found")
        latest = self.turns.get_latest(user_id)
        if latest is None or turn.id != latest.id:
            # La correzione dello stato ha senso solo sull'ultima stima:
            # lo stato e' gia' avanzato oltre i turni precedenti.
            raise ValueError("feedback_only_on_latest_turn")

        state = self.states.get_for_update(user_id)
        params = ModelParams.from_dict(state.params)

        engine_feedback.apply_feedback(
            params, corretto=corretto, emozione_corretta=emozione_corretta
        )
        self.feedback.create(
            turn_id=turn_id,
            user_id=user_id,
            corretto=corretto,
            emozione_corretta=emozione_corretta,
        )

        consolidated = False
        if params.feedback_count % params.consolidation_every == 0:
            pendenti = self.feedback.list_unconsolidated(user_id)
            buffer = self._costruisci_buffer(params, pendenti)
            engine_feedback.consolidate(params, buffer)
            self.feedback.mark_consolidated([f.id for f in pendenti])
            consolidated = bool(buffer)

        self.states.update_params(
            state,
            params.to_dict(),
            n_turns_trained=params.t,
            feedback_count=params.feedback_count,
        )

        inten = engine_model.emotions.intensities(params.z, params.alpha)
        pad = engine_model.emotions.pad(params.z, params.alpha)
        dominant = engine_model.emotions.dominant_emotions(params.z, params.alpha, k=2)
        return {
            "emotions": {e: round(float(x), 4) for e, x in zip(EMOTIONS, inten)},
            "dominant_emotions": [[n, round(i, 4)] for n, i in dominant],
            "valence": float(pad[0]),
            "arousal": float(pad[1]),
            "dominance": float(pad[2]),
            "label": genera_descrizione(dominant, pad, turn.confidence),
            "feedback_count": params.feedback_count,
            "consolidated": consolidated,
        }

    def _costruisci_buffer(self, params: ModelParams, pendenti) -> list:
        """Buffer di consolidamento: solo le CORREZIONI esplicite
        (corretto=False), il cui target e' ricostruibile dall'emozione
        indicata e il cui vettore feature `u` e' salvato sul turno. Le
        conferme (corretto=True) contribuiscono alla correzione immediata
        dello stato ma non al batch (segnale debole)."""
        buffer = []
        for fb in pendenti:
            if fb.corretto or fb.emozione_corretta is None:
                continue
            turn = self.turns.get(fb.turn_id)
            if turn is None:
                continue
            u = np.array(turn.feature_vector, dtype=float)
            target = engine_feedback.target_da_emozione(
                params.alpha, fb.emozione_corretta
            )
            buffer.append((u, target))
        return buffer

    # ------------------------------------------------------------------
    # Storico / diagnostica / reset / calibrazione
    # ------------------------------------------------------------------
    def list_turns(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[EmotionalTurn]:
        return self.turns.list_by_user(user_id, skip=skip, limit=limit)

    def get_turn(self, user_id: int, turn_id: int) -> EmotionalTurn | None:
        turn = self.turns.get(turn_id)
        if turn is None or turn.user_id != user_id:
            return None
        return turn

    def diagnostics(self, user_id: int) -> dict:
        state = self.states.get(user_id)
        params = ModelParams.from_dict(state.params) if state else load_pretrained()
        return engine_model.diagnostics(params)

    def reset_state(self, user_id: int) -> dict:
        state = self._ensure_state(user_id)
        params = ModelParams.from_dict(state.params)
        engine_model.reset_state(params)
        self.states.update_params(
            state,
            params.to_dict(),
            n_turns_trained=params.t,
            feedback_count=params.feedback_count,
        )
        return engine_model.diagnostics(params)

    def calibrate(
        self, user_id: int, *, testo: str, autore_e_soggetto_coincidono: bool
    ) -> dict:
        """Calibrazione con testo scritto DALLA STESSA persona monitorata
        (bio, post, articoli). L'alternativa che rispetta il consenso allo
        scraping di profili di terzi (non implementato). Ogni frase e'
        processata come turno di calibrazione con digitazione neutra."""
        if not autore_e_soggetto_coincidono:
            raise ValueError("consenso_richiesto")

        import re

        state = self._ensure_state(user_id)
        params = ModelParams.from_dict(state.params)
        frasi = [f.strip() for f in re.split(r"[.!?\n]+", testo) if f.strip()]
        for frase in frasi:
            tf = text_features(frase)
            kf = keystroke_features([0.15, 0.18, 0.16, 0.2])  # stima neutra
            inf = interaction_features(5.0, False, 0, 12)
            u = build_feature_vector(tf, kf, inf)
            engine_model.step(params, u, update=True, learn_rate_scale=LIVE_LEARN_RATE)

        self.states.update_params(
            state,
            params.to_dict(),
            n_turns_trained=params.t,
            feedback_count=params.feedback_count,
        )
        return {"frasi_processate": len(frasi), **engine_model.diagnostics(params)}
