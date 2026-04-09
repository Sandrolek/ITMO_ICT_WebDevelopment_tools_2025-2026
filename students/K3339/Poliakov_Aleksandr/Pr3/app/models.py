from enum import Enum
from datetime import date
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


# --- Link table (many-to-many) with extra field ---

class TransactionCategory(SQLModel, table=True):
    transaction_id: int = Field(foreign_key="transaction.id", primary_key=True)
    category_id: int = Field(foreign_key="category.id", primary_key=True)
    is_primary: bool = Field(default=False)


# --- Main tables ---

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str

    accounts: list["Account"] = Relationship(back_populates="user")


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: float = 0.0
    currency: str = "RUB"
    user_id: int = Field(foreign_key="user.id")

    user: Optional[User] = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(back_populates="account")


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    type: TransactionType

    transactions: list["Transaction"] = Relationship(
        back_populates="categories", link_model=TransactionCategory
    )


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    description: Optional[str] = None
    date: date
    type: TransactionType
    account_id: int = Field(foreign_key="account.id")

    account: Optional[Account] = Relationship(back_populates="transactions")
    categories: list[Category] = Relationship(
        back_populates="transactions", link_model=TransactionCategory
    )


# --- Read schemas ---

class CategoryRead(SQLModel):
    id: int
    name: str
    description: Optional[str]
    type: TransactionType


class TransactionRead(SQLModel):
    id: int
    amount: float
    description: Optional[str]
    date: date
    type: TransactionType
    account_id: int
    categories: list[CategoryRead] = []


class AccountRead(SQLModel):
    id: int
    name: str
    balance: float
    currency: str
    user_id: int
    transactions: list[TransactionRead] = []


class UserRead(SQLModel):
    id: int
    username: str
    email: str
    accounts: list[AccountRead] = []


# --- Create/Update schemas ---

class UserCreate(SQLModel):
    username: str
    email: str


class AccountCreate(SQLModel):
    name: str
    balance: float = 0.0
    currency: str = "RUB"
    user_id: int


class AccountUpdate(SQLModel):
    name: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None


class CategoryCreate(SQLModel):
    name: str
    description: Optional[str] = None
    type: TransactionType


class TransactionCreate(SQLModel):
    amount: float
    description: Optional[str] = None
    date: date
    type: TransactionType
    account_id: int
    category_ids: list[int] = []
