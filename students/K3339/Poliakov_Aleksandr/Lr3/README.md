# Лабораторная 3 — Docker, HTTP-вызов парсера и очередь Celery

Оркестрация объединяет FastAPI-приложение из Lr1, парсер из Lr2, PostgreSQL,
Redis и Celery-воркер в одном `docker-compose.yml`.

## Сервисы

| Сервис   | Порт | Роль |
|----------|------|------|
| `db`     | 5432 | PostgreSQL `finance_db` |
| `api`    | 8000 | Приложение Lr1 + роутер `/parser` |
| `parser` | 8001 | Отдельный FastAPI-сервис парсера |
| `redis`  | 6379 | Брокер и backend результатов Celery |
| `worker` | —    | Celery-воркер (фоновый парсинг) |

Вся конфигурация (DB_URL, PARSER_URL, CELERY_*) задана прямо в
`docker-compose.yml` в секциях `environment` — отдельный `.env` не требуется.

## Запуск

```bash
cd Lr3
docker compose up --build
```

## Проверка

Синхронный вызов парсера через основное приложение (Задача 2):

```bash
curl -X POST "http://localhost:8000/parser/parse?url=https://www.python.org/"
```

Асинхронный вызов через очередь (Задача 3):

```bash
# поставить задачу в очередь
curl -X POST "http://localhost:8000/parser/parse/async?url=https://pypi.org/"
# -> {"task_id": "...", "status": "queued"}

# узнать результат по task_id
curl "http://localhost:8000/parser/parse/async/<task_id>"
# -> {"task_id": "...", "status": "SUCCESS", "result": {"url": ..., "title": ...}}
```

Прямой вызов сервиса-парсера (минуя api):

```bash
curl -X POST "http://localhost:8001/parse?url=https://example.com/"
```

Содержимое таблицы `parsed_page`:

```bash
docker compose exec db psql -U postgres -d finance_db \
  -c "select url, title, parser_type from parsed_page;"
```

Swagger: `http://localhost:8000/docs` (роутер `parser`) и `http://localhost:8001/docs`.
