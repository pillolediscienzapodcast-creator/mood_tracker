from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Emotion(str, Enum):
    """Le 8 emozioni di base del modello (Plutchik)."""

    gioia = "gioia"
    fiducia = "fiducia"
    paura = "paura"
    sorpresa = "sorpresa"
    tristezza = "tristezza"
    disgusto = "disgusto"
    rabbia = "rabbia"
    anticipazione = "anticipazione"


class TurnCreate(BaseModel):
    """Input di un turno: testo + segnali comportamentali."""

    text: str = Field(min_length=1, max_length=2000)
    keydown_times: list[float] = Field(
        default_factory=list,
        description="Timestamp assoluti (s) dei tasti (<2 => nessun segnale).",
    )
    backspace_count: int = Field(default=0, ge=0)
    response_latency_s: float = Field(default=5.0, ge=0)
    is_followup: bool = False
    followup_depth: int = Field(default=0, ge=0)
    hour_of_day: Optional[int] = Field(default=None, ge=0, le=23)


class TurnRead(BaseModel):
    """Stima emotiva prodotta per un turno."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    emotions: dict[str, float]
    dominant_emotions: list[tuple[str, float]]
    valence: float
    arousal: float
    dominance: float
    confidence: float
    label: str
    no_lexicon_match: bool


class FeedbackCreate(BaseModel):
    """Feedback umano sull'ultima stima."""

    corretto: bool
    emozione_corretta: Optional[Emotion] = None

    @model_validator(mode="after")
    def _valida_emozione(self) -> "FeedbackCreate":
        if not self.corretto and self.emozione_corretta is None:
            raise ValueError("emozione_corretta e' obbligatoria quando corretto=False")
        if self.corretto and self.emozione_corretta is not None:
            raise ValueError("emozione_corretta non va indicata quando corretto=True")
        return self


class FeedbackRead(BaseModel):
    """Stato emotivo corrente dopo l'applicazione del feedback."""

    emotions: dict[str, float]
    dominant_emotions: list[tuple[str, float]]
    valence: float
    arousal: float
    dominance: float
    label: str
    feedback_count: int
    consolidated: bool


class CalibrationRequest(BaseModel):
    """Calibrazione con testo proprio (richiede consenso esplicito)."""

    testo: str = Field(min_length=1)
    autore_e_soggetto_coincidono: bool

    @model_validator(mode="after")
    def _valida_consenso(self) -> "CalibrationRequest":
        if not self.autore_e_soggetto_coincidono:
            raise ValueError(
                "La calibrazione va usata solo con testo scritto dalla stessa persona "
                "monitorata, con il suo consenso."
            )
        return self


class ModelDiagnostics(BaseModel):
    model_config = ConfigDict(extra="allow")

    model_version: str
    turni_processati: int
    feedback_ricevuti: int
    norma_B: float
    norma_C: float
    traccia_P: float
    alpha: float
    baseline_intensita: list[float]
    baseline_saturato: bool


class CalibrationResult(ModelDiagnostics):
    frasi_processate: int
