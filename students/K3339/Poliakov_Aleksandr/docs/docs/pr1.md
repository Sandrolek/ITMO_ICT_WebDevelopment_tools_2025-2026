# Практика 1 — Базовый FastAPI CRUD

**Папка:** [`Pr1/`](https://github.com/Sandrolek/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lr1/students/K3339/Poliakov_Aleksandr/Pr1)

CRUD-приложение с хранением данных в памяти (без БД). Демонстрирует базовые возможности FastAPI и Pydantic-модели с вложенными объектами.

## Модели (`models.py`)

```python
from enum import Enum
from pydantic import BaseModel
from datetime import date
from typing import Optional


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


class Category(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class Transaction(BaseModel):
    id: int
    amount: float
    description: Optional[str] = None
    date: date
    type: TransactionType
    category: Optional[Category] = None  # вложенный объект


class Account(BaseModel):
    id: int
    name: str
    balance: float
    currency: str = "RUB"
    transactions: list[Transaction] = []  # список вложенных объектов
```

## Эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/accounts` | Все счета с транзакциями |
| GET | `/accounts/{id}` | Счёт по id |
| POST | `/accounts` | Создать счёт |
| PUT | `/accounts/{id}` | Обновить счёт |
| DELETE | `/accounts/{id}` | Удалить счёт |
| GET | `/transactions` | Все транзакции с категорией |
| POST | `/transactions` | Создать транзакцию |
| GET | `/categories` | Все категории |
| POST | `/categories` | Создать категорию |

## Запуск

```bash
pip install fastapi[all]
uvicorn main:app --reload
```
