# Лабораторная 1 — Сервис управления личными финансами

**Папка:** [`Lr1/`](https://github.com/Sandrolek/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lr1/students/K3339/Poliakov_Aleksandr/Lr1)

Полноценный REST API сервис на FastAPI с PostgreSQL, JWT-аутентификацией и полным CRUD для всех сущностей.

## Структура проекта

```
Lr1/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/        (user, account, category, transaction, budget)
│   ├── schemas/       (user, account, category, transaction, budget)
│   ├── routers/       (auth, accounts, categories, transactions, budgets)
│   ├── auth/          (hashing, jwt, dependencies)
│   └── crud/          (user, account, category, transaction, budget)
├── alembic/
├── alembic.ini
├── requirements.txt
└── .env.example
```

## Подключение к БД (`app/database.py`)

```python
from sqlmodel import SQLModel, Session, create_engine
from app.config import DB_URL

engine = create_engine(DB_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

## Модели данных

### User
```python
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
```

### Account
```python
class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    balance: float = 0.0
    currency: str = "RUB"
    user_id: int = Field(foreign_key="user.id")
    transactions: list["Transaction"] = Relationship(back_populates="account")
```

### Category
```python
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    type: TransactionType  # income | expense
```

### Transaction + TransactionCategory (M:M с доп. полями)
```python
class TransactionCategory(SQLModel, table=True):
    transaction_id: int = Field(foreign_key="transaction.id", primary_key=True)
    category_id: int = Field(foreign_key="category.id", primary_key=True)
    is_primary: bool = Field(default=False)  # доп. поле
    note: Optional[str] = None               # доп. поле

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    description: Optional[str] = None
    date: date
    type: TransactionType
    account_id: int = Field(foreign_key="account.id")
    user_id: int = Field(foreign_key="user.id")
    categories: list["Category"] = Relationship(
        back_populates="transactions", link_model=TransactionCategory
    )
```

### Budget
```python
class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount_limit: float
    spent: float = 0.0
    month: int
    year: int
    category_id: int = Field(foreign_key="category.id")
    user_id: int = Field(foreign_key="user.id")
```

## Аутентификация (JWT, ручная реализация)

### Хэширование паролей (`app/auth/hashing.py`)
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### JWT-токены (`app/auth/jwt.py`)
```python
from jose import jwt
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
```

### Dependency (`app/auth/dependencies.py`)
```python
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = session.get(User, int(payload.get("sub")))
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

## API эндпоинты

### Auth (`/auth`)
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/login` | Логин, возвращает JWT |
| GET | `/auth/me` | Профиль текущего пользователя |
| PATCH | `/auth/me` | Обновление профиля |

### Accounts (`/accounts`)
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/accounts` | Список счетов |
| POST | `/accounts` | Создать счёт |
| GET | `/accounts/{id}` | Счёт с вложенными транзакциями |
| PATCH | `/accounts/{id}` | Обновить счёт |
| DELETE | `/accounts/{id}` | Удалить счёт |

### Categories (`/categories`)
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/categories` | Список категорий |
| POST | `/categories` | Создать категорию |
| GET | `/categories/{id}` | Категория по id |
| PATCH | `/categories/{id}` | Обновить категорию |
| DELETE | `/categories/{id}` | Удалить категорию |

### Transactions (`/transactions`)
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/transactions` | Список транзакций с категориями |
| POST | `/transactions` | Создать транзакцию |
| GET | `/transactions/{id}` | Транзакция с категориями |
| PATCH | `/transactions/{id}` | Обновить транзакцию |
| DELETE | `/transactions/{id}` | Удалить транзакцию |

### Budgets (`/budgets`)
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/budgets` | Список бюджетов с категорией |
| POST | `/budgets` | Создать бюджет |
| GET | `/budgets/{id}` | Бюджет с категорией |
| PATCH | `/budgets/{id}` | Обновить бюджет |
| DELETE | `/budgets/{id}` | Удалить бюджет |

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env  # заполнить DB_URL и JWT_SECRET
alembic upgrade head
uvicorn app.main:app --reload
```

Документация доступна на `http://localhost:8000/docs`
