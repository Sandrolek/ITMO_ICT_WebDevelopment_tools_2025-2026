from __future__ import annotations

import requests
from fastapi import FastAPI, HTTPException

from db import init_db_sync
from parser_core import parse_and_store

app = FastAPI(title="Parser Service")


@app.on_event("startup")
def _startup() -> None:
    init_db_sync()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/parse")
def parse(url: str) -> dict[str, str]:
    try:
        return {"message": "Parsing completed", **parse_and_store(url, "http")}
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc))
