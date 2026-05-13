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
    ├── db.py                    # SQLite: init_db, save_page (UPSERT)
    ├── html_title_parser.py     # извлечение <title> через html.parser
    ├── web_config.py            # DEFAULT_URLS, USER_AGENT
    ├── threading_app.py         # threading + urllib
    ├── multiprocessing_app.py   # multiprocessing + urllib
    ├── asyncio_app.py           # asyncio + aiohttp
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

## Задача 2. Параллельный парсинг сайтов с сохранением в SQLite

### Схема БД

```sql
CREATE TABLE IF NOT EXISTS parsed_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    parser_type TEXT NOT NULL,
    parsed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

`UNIQUE(url) + ON CONFLICT DO UPDATE` — повторный парсинг той же страницы обновит запись, а не сломает прогон. Включён режим `journal_mode=WAL` и `busy_timeout=5000`, чтобы параллельные writer-ы из потоков/процессов не падали с `database is locked`.

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

### Threading

Список URL делится «через интерливинг» (`urls[i::workers]`), каждый поток обрабатывает свой подсписок, общий результат собирается под `threading.Lock`.

```python
def parse_and_save(url, db_path):
    html = fetch_html(url)
    title = extract_title(html)
    save_page(url, title, "threading", db_path)
    return {"url": url, "title": title}
```

Поскольку `urllib.request` отпускает GIL во время сетевого ожидания, потоки реально работают параллельно — это и есть классический случай, где threading хорошо подходит.

### Multiprocessing

Каждому процессу передаётся свой чанк URL и путь к общей БД. Сериализация результатов идёт через `Pool.map`. На запись каждый процесс делает своё короткое подключение к SQLite — за счёт WAL и busy_timeout запись из нескольких процессов работает корректно.

### Asyncio + aiohttp

```python
async def fetch_html(session, url):
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        resp.raise_for_status()
        return await resp.text(errors="replace")
```

Запись в SQLite синхронная, поэтому `save_page` вызывается через `asyncio.to_thread`, чтобы не блокировать event loop.

### Замеры — 8 URL, 4 воркера, 3 повтора

| Подход | Min, сек | Mean, сек | Max, сек | Комментарий |
|---|---:|---:|---:|---|
| threading | 0.947 | 2.283 | 4.908 | Большая дисперсия — один медленный TLS-handshake тянет весь прогон |
| multiprocessing | 0.882 | 0.958 | 1.092 | Стабильно, но оверхед на форк процессов |
| asyncio | 0.574 | 0.598 | 0.641 | Самый быстрый и стабильный — один loop, нет переключения процессов |

> Цифры зависят от сети — поэтому отчётный прогон делался подряд, без долгих пауз.

### Выводы по задаче 2

- I/O-bound задача — `asyncio` хорош ровно потому, что один event-loop держит много конкурентных запросов без создания системных потоков. Здесь он *быстрее* threading.
- `threading` всё ещё работает (urllib отпускает GIL во время ожидания сокета), но имеет большую дисперсию: если один из URL отвечает медленно, отстаёт целый поток-«ведро».
- `multiprocessing` для сетевого парсинга — стрельба из пушки по воробьям: оверхед на спавн процессов сравним со временем самих запросов, а никакой выгоды над потоками нет, потому что мы не упираемся в CPU.
- Узкое место не всегда сеть. SQLite допускает одного writer-а одновременно — если URL-ов много и каждый требует записи, реальный «ускоритель» — это уже не concurrency на стороне Python, а параметры БД (WAL, batch insert).

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

# Task 2
python task2/threading_app.py        --workers 4
python task2/multiprocessing_app.py  --workers 4
python task2/asyncio_app.py          --workers 4

# Task 2 benchmark
python task2/benchmark.py --workers 4 --repeats 3
```

Все три entry-point скрипта для каждой задачи поддерживают `--json` для машинно-читаемого вывода (используется в benchmark.py).
