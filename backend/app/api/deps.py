from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.services import user as user_service


def get_db() -> Generator[Session, None, None]:
    """Fornisce una Session SQLAlchemy per-request e la chiude sempre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_or_404(user_id: int, db: Session = Depends(get_db)) -> User:
    """Risolve l'utente dal path o solleva 404. Riusabile dalle route che
    operano su risorse annidate sotto /users/{user_id}."""
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
