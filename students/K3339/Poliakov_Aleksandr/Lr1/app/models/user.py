from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.transaction import Transaction
    from app.models.budget import Budget


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True)
    hashed_password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    accounts: list["Account"] = Relationship(back_populates="user")
    transactions: list["Transaction"] = Relationship(back_populates="user")
    budgets: list["Budget"] = Relationship(back_populates="user")
