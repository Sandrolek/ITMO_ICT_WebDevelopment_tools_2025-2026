from typing import Optional
from sqlmodel import SQLModel


class AccountCreate(SQLModel):
    name: str
    balance: float = 0.0
    currency: str = "RUB"


class AccountUpdate(SQLModel):
    name: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None


class AccountRead(SQLModel):
    id: int
    name: str
    balance: float
    currency: str
    user_id: int


class TransactionNested(SQLModel):
    id: int
    amount: float
    description: Optional[str]
    date: str
    type: str


class AccountReadWithTransactions(AccountRead):
    transactions: list[TransactionNested] = []
