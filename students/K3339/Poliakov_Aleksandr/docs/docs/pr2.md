# Практика 2 — SQLModel + PostgreSQL

**Папка:** [`Pr2/`](https://github.com/Sandrolek/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lr1/students/K3339/Poliakov_Aleksandr/Pr2)

Подключение PostgreSQL через SQLModel. Реализованы связи one-to-many и many-to-many, вложенное отображение данных через `response_model`.

## Подключение к БД (`connection.py`)

```python
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/finance_db"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

## Модели (`models.py`)

```python
class TransactionCategory(SQLModel, table=True):
    transaction_id: int = Field(foreign_key="transaction.id", primary_key=True)
    category_id: int = Field(foreign_key="category.id", primary_key=True)

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
    type: TransactionType
    transactions: list["Transaction"] = Relationship(
        back_populates="categories", link_model=TransactionCategory
    )

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    date: date
    type: TransactionType
    account_id: int = Field(foreign_key="account.id")
    account: Optional[Account] = Relationship(back_populates="transactions")
    categories: list[Category] = Relationship(
        back_populates="transactions", link_model=TransactionCategory
    )
```

## Связи

- **one-to-many:** User → Account, Account → Transaction
- **many-to-many:** Transaction ↔ Category через `TransactionCategory`

## Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/users` | Создать пользователя |
| GET | `/users` | Список пользователей |
| GET | `/users/{id}` | Пользователь со счетами |
| POST/GET/PATCH/DELETE | `/accounts` | CRUD счетов |
| POST/GET/DELETE | `/categories` | CRUD категорий |
| POST/GET/DELETE | `/transactions` | CRUD транзакций с категориями |

## Запуск

```bash
pip install fastapi[all] sqlmodel psycopg2-binary
uvicorn main:app --reload
```
