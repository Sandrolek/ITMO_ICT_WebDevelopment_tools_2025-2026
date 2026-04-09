from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transaction import Transaction


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: float = 0.0
    currency: str = "RUB"
    user_id: int = Field(foreign_key="user.id")

    user: Optional["User"] = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(back_populates="account")
