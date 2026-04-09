from enum import Enum
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.transaction import Transaction, TransactionCategory


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    type: TransactionType

    transactions: list["Transaction"] = Relationship(
        back_populates="categories", link_model="TransactionCategory"
    )
