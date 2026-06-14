from __future__ import annotations

import os

from celery import Celery
from celery.signals import worker_ready

from db import init_db_sync
from parser_core import parse_and_store

celery = Celery(
    "parser",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
)


@worker_ready.connect
def _ensure_schema(**_kwargs) -> None:
    init_db_sync()


@celery.task(name="parse_url")
def parse_url(url: str) -> dict[str, str]:
    return parse_and_store(url, "celery")
