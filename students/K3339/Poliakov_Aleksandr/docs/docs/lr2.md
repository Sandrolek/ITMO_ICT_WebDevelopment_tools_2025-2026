# Лабораторная 2 — Потоки, процессы, асинхронность

**Папка:** [`Lr2/`](https://github.com/Sandrolek/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lr1/students/K3339/Poliakov_Aleksandr/Lr2)

Сделал две задачи: суммирование чисел и параллельный парсинг сайтов. Каждую — в трёх вариантах (`threading`, `multiprocessing`, `asyncio`) и сравнил времена.

## Структура проекта

```
Lr2/
├── requirements.txt
├── task1/
│   ├── common_sum.py            # split_range, arithmetic_sum, loop_sum
│   ├── threading_app.py
│   ├── multiprocessing_app.py
│   ├── asyncio_app.py
│   └── benchmark.py
└── task2/
    ├── config.py                # DB_URL из env/.env, sync + async URL
    ├── models.py                # SQLModel ParsedPage
    ├── db.py                    # init/save sync (psycopg2) и async (asyncpg)
    ├── html_title_parser.py     # извлечение <title> через html.parser
    ├── web_config.py            # DEFAULT_URLS, USER_AGENT
    ├── threading_app.py         # threading + urllib + sync engine
    ├── multiprocessing_app.py   # multiprocessing + urllib + sync engine
    ├── asyncio_app.py           # asyncio + aiohttp + AsyncSession
    └── benchmark.py
```

## Задача 1. Сумма чисел от 1 до 10¹³

Считать честным циклом до 10¹³ невозможно — это часы работы CPU. Поэтому общая логика в `common_sum.py` поддерживает два режима:

- `formula` — арифметическая прогрессия `(s + e) * (e - s + 1) // 2` на каждый чанк. Так считается реальный N = 10¹³ за миллисекунды и получается корректный ответ `50000000000005000000000000`.
- `loop` — обычный `for`-цикл. Нужен только для того, чтобы было что замерять — иначе разницы между подходами на такой быстрой задаче не увидеть.

Разбиение диапазона одинаковое для всех вариантов:

```python
def split_range(start: int, end: int, parts: int) -> list[RangePart]:
    total = end - start + 1
    base, remainder = divmod(total, parts)
    ranges, current = [], start
    for i in range(parts):
        size = base + (1 if i < remainder else 0)
        ranges.append(RangePart(current, current + size - 1))
        current += size
    return ranges
```

### Threading

Поток на каждый чанк, результат пишется в общий список по индексу:

```python
def run(n: int, workers: int, mode: str):
    ranges = split_range(1, n, workers)
    results = [0] * len(ranges)
    threads = []
    for i, part in enumerate(ranges):
        t = threading.Thread(target=lambda i=i, p=part: results.__setitem__(i, calculate_range_sum(p.start, p.end, mode)))
        t.start(); threads.append(t)
    for t in threads: t.join()
    return sum(results)
```

Лока на запись не нужно — каждый поток пишет в свой индекс.

### Multiprocessing

Через `Pool.map`, чтобы не возиться с очередями:

```python
def run(n: int, workers: int, mode: str):
    ranges = split_range(1, n, workers)
    tasks = [(p.start, p.end, mode) for p in ranges]
    with mp.Pool(processes=workers) as pool:
        results = pool.map(worker, tasks)
    return sum(results)
```

### Asyncio

Тут сложнее всего, потому что `asyncio` не параллелит CPU сам по себе. Если просто завернуть цикл в `async def`, выполнение всё равно идёт последовательно — нужно явно отдавать управление loop'у:

```python
async def calculate_sum(start, end, mode):
    if mode == "formula":
        await asyncio.sleep(0)
        return arithmetic_sum(start, end)
    total = 0
    for i, v in enumerate(range(start, end + 1), 1):
        total += v
        if i % 200_000 == 0:
            await asyncio.sleep(0)
    return total
```

`asyncio.sleep(0)` каждые 200к итераций — это и есть «кооперативная» точка переключения. Изначально я ставил её чаще, но это сильно проседало по времени; 200к — нормальный компромисс.

### Замеры — loop mode, N = 5·10⁷, 4 воркера, 3 повтора

| Подход | Min, сек | Mean, сек | Max, сек |
|---|---:|---:|---:|
| threading | 0.947 | 0.955 | 0.960 |
| multiprocessing | 0.269 | 0.278 | 0.283 |
| asyncio | 2.241 | 2.260 | 2.280 |

### Замеры — formula mode, N = 10¹³, 4 воркера, 3 повтора

| Подход | Min, сек | Mean, сек | Max, сек |
|---|---:|---:|---:|
| threading | 0.000412 | 0.000541 | 0.000747 |
| multiprocessing | 0.007685 | 0.007783 | 0.007871 |
| asyncio | 0.000053 | 0.000056 | 0.000060 |

### Что заметил

В `loop`-режиме `multiprocessing` оказался в ~3.5 раза быстрее `threading` — это и есть тот самый эффект GIL: процессы реально считают на разных ядрах, а потоки делят одно. `asyncio` для CPU-нагрузки вообще не годится: оказался в ~2.4 раза медленнее `threading`, потому что `await asyncio.sleep(0)` — это не магия, а просто лишние переключения контекста.

В `formula`-режиме самой задачи фактически нет — одна арифметическая операция на чанк. Поэтому выигрывает тот, у кого меньше оверхеда на запуск, и это `asyncio` (один event loop, без потоков и процессов). `multiprocessing` тут аутсайдер — спавнить пул процессов ради `(a+b)*n/2` бессмысленно.

Главный вывод для себя: `asyncio` ≠ параллелизм. Когда нужно реально считать — это `multiprocessing` или нативные расширения.

## Задача 2. Параллельный парсинг сайтов в Postgres из Lr1

Решил писать не в SQLite, а в ту же Postgres-БД, что и Lr1 (`finance_db`, контейнер из `Lr1/docker-compose.yml`). Для `asyncio`-варианта подключение к БД тоже асинхронное — `asyncpg` через `SQLAlchemy[asyncio]`. Для threading/multiprocessing оставил синхронный `psycopg2` + `SQLModel.Session`: совать `asyncio.run()` внутрь потоков и форков смысла нет.

### Запуск Postgres

```bash
cd Lr1
docker compose up -d db
# postgres / postgres / finance_db / localhost:5432
```

Само Lr1-приложение поднимать не нужно — Task 2 ходит в Postgres напрямую.

### Модель

```python
class ParsedPage(SQLModel, table=True):
    __tablename__ = "parsed_page"
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, unique=True)
    title: str
    parser_type: str
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
```

Таблица создаётся на лету через `SQLModel.metadata.create_all` при первом запуске. Миграцию в `Lr1/alembic/` специально не добавлял — иначе Lr1-сервис при `alembic revision --autogenerate` начал бы пытаться удалить «лишнюю» таблицу. Обычный `alembic upgrade head` от этого никак не страдает.

### UPSERT

В обоих стеках одна и та же логика: достать строку по `url`, если есть — обновить, если нет — вставить. Использовать `INSERT ... ON CONFLICT` не стал, потому что хотелось одинакового кода в sync и async ветках, плюс SQLAlchemy-обвязка для onconflict у Postgres получилась бы громоздкой.

### Список страниц

```python
DEFAULT_URLS = [
    "https://example.com/", "https://www.python.org/",
    "https://docs.python.org/3/", "https://pypi.org/",
    "https://www.wikipedia.org/", "https://httpbin.org/html",
    "https://www.sqlite.org/", "https://docs.aiohttp.org/en/stable/",
]
```

### Threading

Делю URL «через интерливинг» (`urls[i::workers]`), один engine на весь процесс, на каждую запись — своя `Session`:

```python
def parse_and_save(url: str) -> dict[str, str]:
    html = fetch_html(url)
    title = extract_title(html)
    save_page_sync(url, title, "threading")
    return {"url": url, "title": title}

def save_page_sync(url, title, parser_type) -> None:
    with Session(get_sync_engine()) as session:
        existing = session.exec(select(ParsedPage).where(ParsedPage.url == url)).first()
        if existing is not None:
            existing.title = title
            existing.parser_type = parser_type
        else:
            session.add(ParsedPage(url=url, title=title, parser_type=parser_type))
        session.commit()
```

`urllib` и `psycopg2` отпускают GIL на сетевом ожидании, так что потоки тут работают «по-настоящему» — это I/O-bound кейс.

### Multiprocessing

Главная ловушка, на которую напоролся: SQLAlchemy `Engine` **не переживает `fork()`**. Если создать engine в родителе, в детях он сломан. Поэтому в `db.py` я сделал engine ленивым — создаётся при первом обращении из текущего процесса:

```python
_sync_engine = None
def get_sync_engine():
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(SYNC_DB_URL, pool_pre_ping=True)
    return _sync_engine
```

А `init_db_sync()` зову один раз в родителе перед `Pool.map`, чтобы таблица гарантированно была:

```python
def run(urls, workers):
    init_db_sync()
    with mp.Pool(processes=workers) as pool:
        nested = pool.map(worker_chunk, split_list(urls, workers))
    return [item for c in nested for item in c]
```

### Asyncio (полный async-стек)

В первой версии я писал в БД через `asyncio.to_thread(save_page, ...)` — это работало, но это псевдо-async: запись всё равно блокировала worker-тред. После переноса на Postgres переписал на `asyncpg` + `AsyncSession`:

```python
async def parse_and_save(url, session):
    html = await fetch_html(session, url)
    title = extract_title(html)
    await save_page_async(url, title, "asyncio")
    return {"url": url, "title": title}

async def save_page_async(url, title, parser_type):
    async with _get_async_factory()() as session:
        result = await session.execute(sa_select(ParsedPage).where(ParsedPage.url == url))
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.title = title
            existing.parser_type = parser_type
        else:
            session.add(ParsedPage(url=url, title=title, parser_type=parser_type))
        await session.commit()
```

Теперь оба ожидания (сеть и БД) идут через event loop, никаких потоков под капотом.

URL подхватываю из `.env` или env-переменной — async-версия получается автоматически подменой префикса драйвера:

```python
SYNC_DB_URL  = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/finance_db")
ASYNC_DB_URL = SYNC_DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
```

### Замеры — 8 URL, 4 воркера, 3 повтора, Postgres из Lr1

| Подход | Min, сек | Mean, сек | Max, сек |
|---|---:|---:|---:|
| threading | 0.867 | 1.092 | 1.540 |
| multiprocessing | 0.881 | 0.894 | 0.919 |
| asyncio | 0.597 | 0.699 | 0.878 |

Цифры заметно скачут между прогонами — это нормально, дисперсию даёт сама сеть. Заметил, что `https://www.wikipedia.org/` иногда возвращает 403 на `aiohttp` (фильтрует по `User-Agent`); `parse_and_save` ловит исключение и пишет `ERROR: ...` в результат — общий прогон от этого не падает.

### Что заметил

`asyncio` стал быстрее всех — теперь полностью «честно» асинхронный (`aiohttp` + `asyncpg`, ноль `asyncio.to_thread`). У `threading` дисперсия большая: если один URL отвечает медленно, целое «ведро» из его чанка отстаёт. У `multiprocessing` стабильность хорошая, но за это платится `fork` + создание `Engine` в каждом процессе — выигрыша над threading в I/O-задаче нет.

После переезда с SQLite на Postgres цифры стали стабильнее: SQLite держит только одного writer'а одновременно, и при параллельной записи это становилось узким местом. У Postgres такой проблемы нет, поэтому теперь видно, что упираемся именно в сеть, а не в БД.

## Запуск

```bash
cd Lr2
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Task 1, формула, N = 10^13
python task1/threading_app.py        --n 10000000000000 --mode formula --workers 4
python task1/multiprocessing_app.py  --n 10000000000000 --mode formula --workers 4
python task1/asyncio_app.py          --n 10000000000000 --mode formula --workers 4

# Task 1, демонстрация CPU-bound
python task1/threading_app.py        --n 50000000 --mode loop --workers 4
python task1/multiprocessing_app.py  --n 50000000 --mode loop --workers 4
python task1/asyncio_app.py          --n 50000000 --mode loop --workers 4

# Task 1 benchmark
python task1/benchmark.py --n 50000000 --mode loop --workers 4 --repeats 3

# Task 2 — сначала поднимаю Postgres из Lr1
(cd ../Lr1 && docker compose up -d db)

python task2/threading_app.py        --workers 4
python task2/multiprocessing_app.py  --workers 4
python task2/asyncio_app.py          --workers 4

# Task 2 benchmark
python task2/benchmark.py --workers 4 --repeats 3
```

Креды БД по умолчанию те же, что у Lr1 (`postgresql://postgres:postgres@localhost:5432/finance_db`). Переопределяется через `DB_URL` или `.env` рядом со скриптами. `--json` поддерживается всеми entry-point скриптами — используется внутри `benchmark.py`.
