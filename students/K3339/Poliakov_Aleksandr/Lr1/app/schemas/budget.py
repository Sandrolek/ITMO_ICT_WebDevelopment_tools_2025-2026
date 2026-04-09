from typing import Optional
from sqlmodel import SQLModel
from app.schemas.category import CategoryRead


class BudgetCreate(SQLModel):
    amount_limit: float
    month: int
    year: int
    category_id: int


class BudgetUpdate(SQLModel):
    amount_limit: Optional[float] = None
    spent: Optional[float] = None
    month: Optional[int] = None
    year: Optional[int] = None


class BudgetRead(SQLModel):
    id: int
    amount_limit: float
    spent: float
    month: int
    year: int
    category_id: int
    user_id: int


class BudgetReadWithCategory(BudgetRead):
    category: Optional[CategoryRead] = None
