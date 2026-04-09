from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category


class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount_limit: float
    spent: float = 0.0
    month: int
    year: int
    category_id: int = Field(foreign_key="category.id")
    user_id: int = Field(foreign_key="user.id")

    user: Optional["User"] = Relationship(back_populates="budgets")
    category: Optional["Category"] = Relationship()
