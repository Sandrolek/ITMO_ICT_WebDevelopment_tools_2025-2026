from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ParsedPage(SQLModel, table=True):
    __tablename__ = "parsed_page"

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, unique=True)
    title: str
    parser_type: str
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
