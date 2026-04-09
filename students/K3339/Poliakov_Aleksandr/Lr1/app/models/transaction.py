from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from app.models.category import TransactionType

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.user import User
    from app.models.category import Category


class TransactionCategory(SQLModel, table=True):
    transaction_id: int = Field(foreign_key="transaction.id", primary_key=True)
    category_id: int = Field(foreign_key="category.id", primary_key=True)
    is_primary: bool = Field(default=False)
    note: Optional[str] = None


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    description: Optional[str] = None
    date: date
    type: TransactionType
    account_id: int = Field(foreign_key="account.id")
    user_id: int = Field(foreign_key="user.id")

    account: Optional["Account"] = Relationship(back_populates="transactions")
    user: Optional["User"] = Relationship(back_populates="transactions")
    categories: list["Category"] = Relationship(
        back_populates="transactions", link_model=TransactionCategory
    )
