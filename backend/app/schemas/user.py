from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    name: str = Field(max_length=100)
    email: str = Field(max_length=255)


class UserCreate(UserBase):
    """Payload per la creazione di un utente."""


class UserUpdate(BaseModel):
    """Payload per l'aggiornamento: tutti i campi opzionali."""

    name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)


class UserRead(UserBase):
    """Rappresentazione in output di un utente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
