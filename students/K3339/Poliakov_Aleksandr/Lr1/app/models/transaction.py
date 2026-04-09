from datetime import date
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from app.models.category import TransactionType
from app.models.links import TransactionCategory

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.user import User
    from app.models.category import Category


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    description: Optional[str] = None
    date: date
    location: Optional[str] = None
    type: TransactionType
    account_id: int = Field(foreign_key="account.id")
    user_id: int = Field(foreign_key="user.id")

    account: Optional["Account"] = Relationship(back_populates="transactions")
    user: Optional["User"] = Relationship(back_populates="transactions")
    categories: list["Category"] = Relationship(
        back_populates="transactions", link_model=TransactionCategory
    )
