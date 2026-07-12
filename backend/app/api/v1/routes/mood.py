"""Endpoint del dominio NOEMA (tracciamento emotivo), annidati sotto
/users/{user_id}. Le route gestiscono il confine di transazione: i servizi
fanno flush, la route committa in caso di successo.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_user_or_404
from app.models.user import User
from app.schemas.mood import (
    CalibrationRequest,
    CalibrationResult,
    FeedbackCreate,
    FeedbackRead,
    ModelDiagnostics,
    TurnCreate,
    TurnRead,
)
from app.services.mood import MoodService

router = APIRouter()


@router.post(
    "/{user_id}/turns", response_model=TurnRead, status_code=status.HTTP_201_CREATED
)
def ingest_turn(
    user_id: int,
    data: TurnCreate,
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    turn = MoodService(db).ingest_turn(
        user_id,
        text=data.text,
        keydown_times=data.keydown_times,
        backspace_count=data.backspace_count,
        response_latency_s=data.response_latency_s,
        is_followup=data.is_followup,
        followup_depth=data.followup_depth,
        hour_of_day=data.hour_of_day,
    )
    db.commit()
    db.refresh(turn)
    return turn


@router.get("/{user_id}/turns", response_model=List[TurnRead])
def list_turns(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    return MoodService(db).list_turns(user_id, skip=skip, limit=limit)


@router.get("/{user_id}/turns/{turn_id}", response_model=TurnRead)
def read_turn(
    user_id: int,
    turn_id: int,
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    turn = MoodService(db).get_turn(user_id, turn_id)
    if turn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Turn not found"
        )
    return turn


@router.post("/{user_id}/turns/{turn_id}/feedback", response_model=FeedbackRead)
def provide_feedback(
    user_id: int,
    turn_id: int,
    data: FeedbackCreate,
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    service = MoodService(db)
    try:
        result = service.apply_feedback(
            user_id,
            turn_id,
            corretto=data.corretto,
            emozione_corretta=data.emozione_corretta.value
            if data.emozione_corretta
            else None,
        )
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Turn not found"
        )
    except ValueError as exc:
        detail = (
            "Il feedback puo' essere dato solo sull'ultimo turno"
            if str(exc) == "feedback_only_on_latest_turn"
            else str(exc)
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    db.commit()
    return result


@router.get("/{user_id}/model", response_model=ModelDiagnostics)
def model_diagnostics(
    user_id: int, user: User = Depends(get_user_or_404), db: Session = Depends(get_db)
):
    return MoodService(db).diagnostics(user_id)


@router.post("/{user_id}/model/reset", response_model=ModelDiagnostics)
def reset_model(
    user_id: int, user: User = Depends(get_user_or_404), db: Session = Depends(get_db)
):
    diag = MoodService(db).reset_state(user_id)
    db.commit()
    return diag


@router.post("/{user_id}/calibrate", response_model=CalibrationResult)
def calibrate(
    user_id: int,
    data: CalibrationRequest,
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    result = MoodService(db).calibrate(
        user_id,
        testo=data.testo,
        autore_e_soggetto_coincidono=data.autore_e_soggetto_coincidono,
    )
    db.commit()
    return result
