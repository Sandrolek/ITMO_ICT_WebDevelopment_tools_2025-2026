from __future__ import annotations

from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import Session, SQLModel, create_engine, select

from config import ASYNC_DB_URL, SYNC_DB_URL
from models import ParsedPage


_sync_engine = None


def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(SYNC_DB_URL, pool_pre_ping=True)
    return _sync_engine


def init_db_sync() -> None:
    SQLModel.metadata.create_all(get_sync_engine())


def save_page_sync(url: str, title: str, parser_type: str) -> None:
    with Session(get_sync_engine()) as session:
        existing = session.exec(
            select(ParsedPage).where(ParsedPage.url == url)
        ).first()
        if existing is not None:
            existing.title = title
            existing.parser_type = parser_type
        else:
            session.add(ParsedPage(url=url, title=title, parser_type=parser_type))
        session.commit()


def dispose_sync_engine() -> None:
    global _sync_engine
    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None


_async_engine = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_async_factory() -> async_sessionmaker[AsyncSession]:
    global _async_engine, _async_session_factory
    if _async_session_factory is None:
        _async_engine = create_async_engine(ASYNC_DB_URL, pool_pre_ping=True)
        _async_session_factory = async_sessionmaker(
            _async_engine, expire_on_commit=False, class_=AsyncSession
        )
    return _async_session_factory


async def init_db_async() -> None:
    _get_async_factory()
    assert _async_engine is not None
    async with _async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def save_page_async(url: str, title: str, parser_type: str) -> None:
    factory = _get_async_factory()
    async with factory() as session:
        result = await session.execute(
            sa_select(ParsedPage).where(ParsedPage.url == url)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.title = title
            existing.parser_type = parser_type
        else:
            session.add(ParsedPage(url=url, title=title, parser_type=parser_type))
        await session.commit()


async def dispose_async_engine() -> None:
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None
