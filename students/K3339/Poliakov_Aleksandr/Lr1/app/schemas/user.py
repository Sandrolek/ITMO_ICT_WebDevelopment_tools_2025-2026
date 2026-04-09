from typing import Optional
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserLogin(SQLModel):
    username: str
    password: str


class UserRead(SQLModel):
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]


class UserUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
