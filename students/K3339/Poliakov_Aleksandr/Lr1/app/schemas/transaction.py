from datetime import date
from typing import Optional
from sqlmodel import SQLModel
from app.models.category import TransactionType
from app.schemas.category import CategoryRead


class TransactionCreate(SQLModel):
    amount: float
    description: Optional[str] = None
    date: date
    type: TransactionType
    account_id: int
    category_ids: list[int] = []


class TransactionUpdate(SQLModel):
    amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[date] = None
    type: Optional[TransactionType] = None


class TransactionRead(SQLModel):
    id: int
    amount: float
    description: Optional[str]
    date: date
    type: TransactionType
    account_id: int
    user_id: int


class TransactionReadWithCategories(TransactionRead):
    categories: list[CategoryRead] = []
