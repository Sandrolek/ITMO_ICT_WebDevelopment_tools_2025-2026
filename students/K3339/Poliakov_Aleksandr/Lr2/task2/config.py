from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/finance_db"

SYNC_DB_URL = os.getenv("DB_URL", DEFAULT_DB_URL)
ASYNC_DB_URL = SYNC_DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
