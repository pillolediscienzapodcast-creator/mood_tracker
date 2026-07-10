from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    stmt = select(User).order_by(User.id).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.get(User, user_id)


def create_user(db: Session, data: UserCreate) -> User:
    user = User(name=data.name, email=data.email)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    values = data.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(user, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
