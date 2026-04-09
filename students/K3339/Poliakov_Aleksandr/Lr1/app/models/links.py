from typing import Optional
from sqlmodel import SQLModel, Field


class TransactionCategory(SQLModel, table=True):
    transaction_id: int = Field(foreign_key="transaction.id", primary_key=True)
    category_id: int = Field(foreign_key="category.id", primary_key=True)
    is_primary: bool = Field(default=False)
    note: Optional[str] = None
