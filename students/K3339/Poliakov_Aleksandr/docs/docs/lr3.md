# Лабораторная 3 — Docker, HTTP-вызов парсера и очередь Celery

**Папка:** [`Lr3/`](https://github.com/Sandrolek/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lr1/students/K3339/Poliakov_Aleksandr/Lr3)

Объединение наработок Lr1 (FastAPI + PostgreSQL) и Lr2 (парсер `<title>`) в одну
Docker-оркестрацию. Парсер вынесен в отдельный сервис, вызывается из основного
приложения по HTTP, а также в фоне через очередь Celery + Redis.

## Архитектура

| Сервис   | Сборка / образ                                | Порт | Роль |
|----------|-----------------------------------------------|------|------|
| `db`     | `postgres:16`                                 | 5432 | БД `finance_db` |
| `api`    | `build: ../Lr1`                               | 8000 | Приложение Lr1 + роутер `/parser` |
| `parser` | `build: ..` (`Lr3/parser/Dockerfile`)         | 8001 | Отдельный FastAPI-сервис парсера |
| `redis`  | `redis:7`                                     | 6379 | Брокер и backend результатов Celery |
| `worker` | тот же образ, что `parser`                    | —    | Celery-воркер (фоновый парсинг) |

Поток данных:

- **Синхронно (Задача 2):** клиент → `api` `POST /parser/parse` → httpx → `parser` `POST /parse` → fetch + extract + save в `db` → ответ клиенту.
- **Асинхронно (Задача 3):** клиент → `api` `POST /parser/parse/async` → `send_task` в `redis` → `worker` выполняет задачу → результат в backend → клиент опрашивает `GET /parser/parse/async/{task_id}`.

## Структура проекта

```
Lr3/
├── docker-compose.yml      # db, api, parser, redis, worker
├── README.md
└── parser/
    ├── Dockerfile          # копирует Lr2/task2/*.py + Lr3/parser/*.py в образ
    ├── requirements.txt
    ├── parser_core.py      # parse_and_store(url) — единый источник логики
    ├── main.py             # FastAPI-сервис: POST /parse, GET /health
    └── celery_app.py       # Celery + задача parse_url
```

## Переиспользование парсера из Lr2

Модули Lr2 (`html_title_parser.py`, `db.py`, `models.py`, `config.py`,
`web_config.py`) импортируются как есть. Общая функция вызывается и HTTP-сервисом,
и Celery-задачей — единый источник логики, без дублирования.

```python
# parser/parser_core.py
import requests
from db import save_page_sync           # из Lr2/task2
from html_title_parser import extract_title  # из Lr2/task2
from web_config import USER_AGENT             # из Lr2/task2

def parse_and_store(url: str, parser_type: str = "http") -> dict[str, str]:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    response.raise_for_status()
    title = extract_title(response.text)
    save_page_sync(url, title, parser_type)
    return {"url": url, "title": title}
```

Парсер сделан синхронным (`requests` + `save_page_sync`), поэтому одна и та же
функция работает и в FastAPI-сервисе, и в Celery-воркере.

## Задача 1 — сервис-парсер и Dockerfile

Отдельное FastAPI-приложение, вызываемое по HTTP:

```python
# parser/main.py
from fastapi import FastAPI, HTTPException
import requests
from db import init_db_sync
from parser_core import parse_and_store

app = FastAPI(title="Parser Service")

@app.on_event("startup")
def _startup():
    init_db_sync()   # создаёт таблицу parsed_page (идемпотентно)

@app.post("/parse")
def parse(url: str):
    try:
        return {"message": "Parsing completed", **parse_and_store(url, "http")}
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=str(exc))
```

Один Dockerfile обслуживает и `parser`, и `worker` (команда задаётся в compose).
Build-контекст — каталог `Poliakov_Aleksandr/`, поэтому в образ попадает код Lr2:

```dockerfile
# parser/Dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY Lr3/parser/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY Lr2/task2/ ./      # парсер из Lr2
COPY Lr3/parser/ ./     # интеграционный код Lr3
```

## Задача 2 — вызов парсера из основного приложения

В приложение Lr1 добавлен роутер `/parser`. Синхронный эндпоинт проксирует
запрос в сервис-парсер (отдельный контейнер) и возвращает результат клиенту:

```python
# Lr1/app/routers/parser.py
import os, httpx
from fastapi import APIRouter, HTTPException
from celery import Celery

router = APIRouter(prefix="/parser", tags=["parser"])
PARSER_URL = os.getenv("PARSER_URL", "http://parser:8001")
celery = Celery("client",
                broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
                backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"))

@router.post("/parse")                       # Задача 2 — синхронно через HTTP
async def parse_sync(url: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{PARSER_URL}/parse", params={"url": url})
        r.raise_for_status()
        return r.json()
```

## Задача 3 — очередь Celery + Redis

Фоновая задача и конфигурация Celery:

```python
# parser/celery_app.py
import os
from celery import Celery
from celery.signals import worker_ready
from db import init_db_sync
from parser_core import parse_and_store

celery = Celery("parser",
                broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
                backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"))

@worker_ready.connect
def _ensure_schema(**_):
    init_db_sync()

@celery.task(name="parse_url")
def parse_url(url: str) -> dict:
    return parse_and_store(url, "celery")
```

Эндпоинты постановки задачи и получения результата в роутере `/parser`:

```python
@router.post("/parse/async")                 # поставить в очередь
def parse_async(url: str):
    task = celery.send_task("parse_url", args=[url])
    return {"task_id": task.id, "status": "queued"}

@router.get("/parse/async/{task_id}")        # узнать статус/результат
def parse_result(task_id: str):
    res = celery.AsyncResult(task_id)
    return {"task_id": task_id, "status": res.status,
            "result": res.result if res.successful() else None}
```

`api` ставит задачу по имени (`send_task("parse_url", ...)`) — ему не нужен код
задачи, только адрес брокера.

## docker-compose

Все пять сервисов в одной сети, конфигурация — в секциях `environment`:

```yaml
services:
  db:      # postgres:16, healthcheck pg_isready, volume pgdata
  redis:   # redis:7
  api:
    build: { context: ../Lr1 }
    environment:
      DB_URL: postgresql://postgres:postgres@db:5432/finance_db
      PARSER_URL: http://parser:8001
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    depends_on: [db (healthy), parser, redis]
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  parser:
    build: { context: .., dockerfile: Lr3/parser/Dockerfile }
    command: uvicorn main:app --host 0.0.0.0 --port 8001
  worker:
    build: { context: .., dockerfile: Lr3/parser/Dockerfile }
    command: celery -A celery_app.celery worker --loglevel=info
```

## Запуск и проверка

```bash
cd Lr3
docker compose up --build
```

Синхронный вызов (Задача 2):

```bash
curl -X POST "http://localhost:8000/parser/parse?url=https://www.python.org/"
# {"message":"Parsing completed","url":"https://www.python.org/","title":"Welcome to Python.org"}
```

Асинхронный вызов через очередь (Задача 3):

```bash
curl -X POST "http://localhost:8000/parser/parse/async?url=https://pypi.org/"
# {"task_id":"...","status":"queued"}

curl "http://localhost:8000/parser/parse/async/<task_id>"
# {"task_id":"...","status":"SUCCESS","result":{"url":"https://pypi.org/","title":"PyPI · ..."}}
```

Содержимое таблицы:

```bash
docker compose exec db psql -U postgres -d finance_db \
  -c "select url, title, parser_type from parsed_page;"
```

Swagger: `http://localhost:8000/docs` (роутер `parser`) и `http://localhost:8001/docs`.

## Что заметил

- Build-контекст `..` для `parser`/`worker` позволил переиспользовать код Lr2 без
  копирования и дублирования — плоские импорты Lr2 (`from db import ...`)
  работают, потому что модули копируются в рабочий каталог образа.
- Один образ на `parser` и `worker` — экономия на сборке; разница только в команде
  запуска (`uvicorn` против `celery worker`).
- Синхронный парсер (`requests`) удобнее асинхронного для этой задачи: одна
  функция `parse_and_store` переиспользуется и в FastAPI, и в Celery, где код всё
  равно синхронный.
- `send_task` по имени развязывает `api` и реализацию задачи: основному
  приложению достаточно знать только адрес брокера.
- В команде `api` не используется `alembic upgrade head`: единственная миграция
  Lr1 (add location) рассчитана на уже существующие таблицы и падает на чистом
  томе. Схему создаёт сам app при старте через `on_startup` → `init_db`
  (`SQLModel.metadata.create_all`), поэтому отдельный шаг миграций здесь не нужен.
