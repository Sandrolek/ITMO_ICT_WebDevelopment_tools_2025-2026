# Практика 3 — Alembic, .env, структура проекта

**Папка:** [`Pr3/`](https://github.com/Sandrolek/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lr1/students/K3339/Poliakov_Aleksandr/Pr3)

Добавлены миграции через Alembic, переменные окружения через `.env`, структура проекта вынесена в папку `app/`.

## Структура

```
Pr3/
├── app/
│   ├── main.py
│   ├── connection.py
│   └── models.py
├── migrations/
│   ├── env.py
│   ├── versions/
│   └── script.py.mako
├── alembic.ini
├── .env.example
└── .gitignore
```

## Подключение к БД через .env (`app/connection.py`)

```python
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine

load_dotenv()
DATABASE_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/finance_db")
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
```

## Alembic с .env (`migrations/env.py`)

```python
import os
from dotenv import load_dotenv
from sqlmodel import SQLModel
from app.models import *  # noqa

load_dotenv()
config.set_main_option("sqlalchemy.url", os.getenv("DB_URL", ""))
target_metadata = SQLModel.metadata
```

Ключевое: `alembic.ini` оставляет `sqlalchemy.url =` пустым, URL подставляется из `.env` в `env.py`.

## Ассоциативная сущность с дополнительным полем

```python
class TransactionCategory(SQLModel, table=True):
    transaction_id: int = Field(foreign_key="transaction.id", primary_key=True)
    category_id: int = Field(foreign_key="category.id", primary_key=True)
    is_primary: bool = Field(default=False)  # дополнительное поле
```

## .gitignore

```
*.env
!.env.example
__pycache__
venv
.vscode
.idea
```

## Миграции

```bash
pip install alembic python-dotenv
alembic revision --autogenerate -m "init"
alembic upgrade head
```
