from __future__ import annotations

import os

import httpx
from celery import Celery
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/parser", tags=["parser"])

PARSER_URL = os.getenv("PARSER_URL", "http://parser:8001")

celery = Celery(
    "client",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
)


@router.post("/parse")
async def parse_sync(url: str):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{PARSER_URL}/parse", params={"url": url})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Parser service error: {exc.response.text}",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Parser service unavailable: {exc}")


@router.post("/parse/async")
def parse_async(url: str):
    task = celery.send_task("parse_url", args=[url])
    return {"task_id": task.id, "status": "queued"}


@router.get("/parse/async/{task_id}")
def parse_result(task_id: str):
    result = celery.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.successful() else None,
    }
