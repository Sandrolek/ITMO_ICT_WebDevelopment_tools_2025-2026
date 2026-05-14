# Лабораторная 2 — Потоки, процессы, асинхронность

**Папка:** [`Lr2/`](https://github.com/Sandrolek/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/lr1/students/K3339/Poliakov_Aleksandr/Lr2)

Цель — практически прочувствовать разницу между `threading`, `multiprocessing` и `asyncio`: где какой подход выигрывает, где упирается в GIL, где помогает asyncio. Лабораторная состоит из двух задач — CPU-bound (сумма чисел) и I/O-bound (параллельный парсинг сайтов).

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

### Общая логика

В `common_sum.py` диапазон `[1, N]` делится на `workers` равных частей; каждая часть считается одним из двух способов:

- `arithmetic_sum(s, e) = (s + e) * (e - s + 1) // 2` — корректно для `N = 10¹³`, где честный `for`-цикл нереалистичен.
- `loop_sum(s, e)` — суммирование в цикле; нужен только для демонстрации CPU-bound нагрузки.

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

Поток для каждой части диапазона, результат пишется в общий список по индексу — без блокировки, потому что разные индексы.

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

CPython держит GIL — в loop-режиме поток за поток поочерёдно исполняют байткод, а не одновременно. Поэтому ускорения над однопоточной версией почти нет.

### Multiprocessing

Несколько процессов, у каждого свой интерпретатор и память. Используется `multiprocessing.Pool.map`:

```python
def run(n: int, workers: int, mode: str):
    ranges = split_range(1, n, workers)
    tasks = [(p.start, p.end, mode) for p in ranges]
    with mp.Pool(processes=workers) as pool:
        results = pool.map(worker, tasks)
    return sum(results)
```

Здесь каждый процесс реально выполняется на своём ядре — GIL не мешает. Цена — оверхед на запуск процессов и сериализацию аргументов через `pickle`.

### Asyncio

`asyncio` не даёт CPU-параллелизма: одна event-loop, переключения только на `await`. Чтобы цикл не зависал на много секунд, добавлены checkpoint-ы:

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

`await asyncio.sleep(0)` отдаёт управление loop'у — это единственный способ кооперативного переключения. На CPU-bound коде это даёт только просадку производительности относительно прямого однопоточного цикла.

### Замеры — loop mode, N = 5·10⁷, 4 воркера, 3 повтора

| Подход | Min, сек | Mean, сек | Max, сек | Комментарий |
|---|---:|---:|---:|---|
| threading | 0.947 | 0.955 | 0.960 | GIL не даёт реального параллелизма на байткоде |
| multiprocessing | 0.269 | 0.278 | 0.283 | Реально работает на нескольких ядрах |
| asyncio | 2.241 | 2.260 | 2.280 | Хуже однопотока — checkpoint-ы добавляют оверхед |

### Замеры — formula mode, N = 10¹³, 4 воркера, 3 повтора

| Подход | Min, сек | Mean, сек | Max, сек | Комментарий |
|---|---:|---:|---:|---|
| threading | 0.000412 | 0.000541 | 0.000747 | Формула — O(1), потоки лишь добавляют чуть оверхеда |
| multiprocessing | 0.007685 | 0.007783 | 0.007871 | Запуск пула процессов дороже самой задачи |
| asyncio | 0.000053 | 0.000056 | 0.000060 | Самое быстрое — почти ничего не делает |

Корректный результат для N = 10¹³: `50000000000005000000000000`.

### Выводы по задаче 1

- На «честной» CPU-bound нагрузке (`loop`) — `multiprocessing` обгоняет `threading` примерно в 3.5 раза, потому что обходит GIL. `asyncio` оказывается *медленнее* однопоточного решения: вытесняющего планирования нет, а checkpoint-ы тормозят.
- На «обходной» нагрузке (`formula`) задача сводится к одной операции на чанк, поэтому выигрывает подход с наименьшим оверхедом запуска — `asyncio`. У `multiprocessing` оверхед запуска пула на два порядка больше самой задачи.
- Главный вывод: `asyncio` ≠ параллелизм. Для CPU нужны процессы или нативные расширения, а потоки полезны только если время реально проводят в ожидании I/O.

## Задача 2. Параллельный парсинг сайтов с сохранением в Postgres из Lr1

В этой задаче результаты пишутся не в локальный SQLite, а в **ту же Postgres-БД, что использует Лабораторная 1** (`finance_db` на `postgres:postgres@localhost:5432`). Для `asyncio`-варианта подключение к БД тоже асинхронное (`asyncpg` + `SQLAlchemy[asyncio]` + `AsyncSession`). Для `threading` и `multiprocessing` подключение остаётся синхронным (`psycopg2` + `Session`) — это естественно для соответствующих моделей параллелизма.

### Запуск Postgres

```bash
cd Lr1
docker compose up -d db          # сервис db из docker-compose.yml Lr1
# параметры по умолчанию: postgres / postgres / finance_db / localhost:5432
```

Lr1-app поднимать не нужно — Task 2 общается с Postgres напрямую.

### Схема и модель

Модель описана через SQLModel в `Lr2/task2/models.py`:

```python
class ParsedPage(SQLModel, table=True):
    __tablename__ = "parsed_page"
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, unique=True)
    title: str
    parser_type: str
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
```

Таблица создаётся через `SQLModel.metadata.create_all` при первом запуске любого из вариантов (`init_db_sync()` или `await init_db_async()`). Миграции для Lr1 мы не правим — поэтому при работе с alembic в Lr1 **не нужно** делать `revision --autogenerate`, иначе оно попытается удалить «лишнюю» таблицу `parsed_page`. Обычное `alembic upgrade head` безопасно.

### UPSERT-семантика

В обоих стеках реализован один и тот же паттерн: `SELECT ... WHERE url = :url` → если строка есть, обновить `title`/`parser_type`, иначе вставить новую. Это даёт идемпотентность для повторных прогонов и нормально работает под параллельной записью благодаря `UNIQUE(url)`.

### Список страниц

```python
DEFAULT_URLS = [
    "https://example.com/", "https://www.python.org/",
    "https://docs.python.org/3/", "https://pypi.org/",
    "https://www.wikipedia.org/", "https://httpbin.org/html",
    "https://www.sqlite.org/", "https://docs.aiohttp.org/en/stable/",
]
```

### Парсинг заголовка

`html_title_parser.TitleParser` наследуется от `html.parser.HTMLParser` и собирает текст между `<title>...</title>`. Если тег отсутствует — возвращается `<no title>`.

### Threading (sync engine)

Список URL делится «через интерливинг» (`urls[i::workers]`), каждый поток обрабатывает свой подсписок, общий результат собирается под `threading.Lock`. Запись идёт через общий `Engine` SQLAlchemy — он thread-safe, каждая сессия получает отдельное соединение из пула.

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

Поскольку `urllib.request` и `psycopg2` отпускают GIL во время сетевого ожидания, потоки реально работают параллельно — это классический случай, где threading хорошо подходит.

### Multiprocessing (sync engine, ленивый на каждый процесс)

`Engine` создаётся лениво при первом вызове `save_page_sync` — это важно: SQLAlchemy connection pool **не переживает fork**, поэтому каждый worker-процесс должен открыть свой пул сам. `init_db_sync()` вызывается в родительском процессе **до** `Pool.map`, чтобы таблица гарантированно существовала к моменту первой записи.

```python
def run(urls, workers):
    init_db_sync()
    chunks = split_list(urls, workers)
    with mp.Pool(processes=workers) as pool:
        nested = pool.map(worker_chunk, chunks)
    return [item for c in nested for item in c]
```

### Asyncio + aiohttp + asyncpg (полный async-стек)

Для асинхронного варианта подключение к БД — тоже асинхронное: `asyncpg` через `SQLAlchemy[asyncio]` (`create_async_engine` + `AsyncSession`). Никаких `asyncio.to_thread` для записи не остаётся — оба ожидания, и сетевое, и БД-шное, идут через event loop.

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

Конфиг URL автоматически берёт сначала `DB_URL` из env (или `.env` через `python-dotenv`), а для async-варианта подменяет `postgresql://` на `postgresql+asyncpg://`:

```python
SYNC_DB_URL  = os.getenv("DB_URL", "postgresql://postgres:postgres@localhost:5432/finance_db")
ASYNC_DB_URL = SYNC_DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
```

### Замеры — 8 URL, 4 воркера, 3 повтора, Postgres из Lr1

| Подход | Min, сек | Mean, сек | Max, сек | Комментарий |
|---|---:|---:|---:|---|
| threading | 0.867 | 1.092 | 1.540 | Большая дисперсия — один медленный URL тянет поток-«ведро» |
| multiprocessing | 0.881 | 0.894 | 0.919 | Стабильно, но платит за `fork` + создание engine в каждом процессе |
| asyncio | 0.597 | 0.699 | 0.878 | Полностью async-стек — самый быстрый |

> Цифры зависят от сети и от того, какие URL вернут 403 (часть сайтов фильтрует user-agent). Сами цифры стабильнее, чем у предыдущей SQLite-версии, потому что Postgres не упирается в single-writer-bottleneck.

### Выводы по задаче 2

- I/O-bound задача — `asyncio` хорош ровно потому, что один event-loop держит много конкурентных запросов без создания системных потоков. С полным async-стеком (`aiohttp` + `asyncpg`) асинхронность работает «честно» от и до — нет ни одного `asyncio.to_thread`.
- `threading` всё ещё работает (urllib и psycopg2 отпускают GIL на сетевом ожидании), но имеет большую дисперсию: если один из URL отвечает медленно, целый поток-«ведро» отстаёт.
- `multiprocessing` для сетевого парсинга — стрельба из пушки по воробьям: оверхед на спавн процессов и инициализацию `Engine` в каждом сравним со временем самих запросов, а никакой выгоды над потоками нет, потому что мы не упираемся в CPU.
- В отличие от SQLite, Postgres нормально держит параллельные writer-ы — узкое место теперь точно сеть, а не БД. Это и видно по тому, что `multiprocessing` перестал быть быстрее `threading`.

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

# Task 2 — сначала поднимаем Postgres из Lr1
(cd ../Lr1 && docker compose up -d db)

python task2/threading_app.py        --workers 4
python task2/multiprocessing_app.py  --workers 4
python task2/asyncio_app.py          --workers 4

# Task 2 benchmark
python task2/benchmark.py --workers 4 --repeats 3
```

Адрес/креды БД по умолчанию — те же, что в Lr1 (`postgresql://postgres:postgres@localhost:5432/finance_db`). Можно переопределить через переменную `DB_URL` или файл `.env` рядом со скриптами.

Все три entry-point скрипта для каждой задачи поддерживают `--json` для машинно-читаемого вывода (используется в benchmark.py).
