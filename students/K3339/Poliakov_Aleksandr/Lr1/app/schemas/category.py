from typing import Optional
from sqlmodel import SQLModel
from app.models.category import TransactionType


class CategoryCreate(SQLModel):
    name: str
    description: Optional[str] = None
    type: TransactionType


class CategoryUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[TransactionType] = None


class CategoryRead(SQLModel):
    id: int
    name: str
    description: Optional[str]
    type: TransactionType
