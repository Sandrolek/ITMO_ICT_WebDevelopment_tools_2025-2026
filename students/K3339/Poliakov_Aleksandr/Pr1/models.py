from enum import Enum
from pydantic import BaseModel
from datetime import date
from typing import Optional


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class Category(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class Transaction(BaseModel):
    id: int
    amount: float
    description: Optional[str] = None
    date: date
    type: TransactionType
    category: Optional[Category] = None


class TransactionCreate(BaseModel):
    amount: float
    description: Optional[str] = None
    date: date
    type: TransactionType
    category_id: Optional[int] = None


class Account(BaseModel):
    id: int
    name: str
    balance: float
    currency: str = "RUB"
    transactions: list[Transaction] = []


class AccountCreate(BaseModel):
    name: str
    balance: float = 0.0
    currency: str = "RUB"


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
