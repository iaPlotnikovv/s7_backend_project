# Flight Passenger Analysis Service

Микросервисная система для кластеризации пассажиров авиарейсов на основе истории перелётов.  
Данные о рейсах → текстовая сериализация → эмбеддинги → KMeans → UMAP 2D → интерактивный scatter plot.

---

## Как это работает

```
┌─────────────┐     JWT      ┌──────────────────────────────────────────────────────┐
│   Browser   │◄────────────►│  auth-service :8001                                  │
│  (index.html│              │  POST /auth/register                                 │
│   Chart.js) │              │  POST /auth/login                                    │
│             │              │  GET  /auth/me                                       │
└──────┬──────┘              └──────────────────────────────────────────────────────┘
       │
       │ POST /analysis          ┌──────────────────────────────────────────────────┐
       │ GET  /analysis/results  │  analysis-service :8003                          │
       └────────────────────────►│                                                  │
                                 │  1. GET /passengers/flights ──────────────────┐  │
                                 │  2. serialize flights → text                  │  │
                                 │  3. Sentence Transformers → embeddings        │  │
                                 │  4. KMeans → cluster label                    │  │
                                 │  5. UMAP → x, y coordinates                  │  │
                                 │  6. upsert → results table                   │  │
                                 └──────────────────────────────────────────────┼──┘
                                                                                │
                                 ┌──────────────────────────────────────────────▼──┐
                                 │  passenger-service (internal)                    │
                                 │  GET /passengers/flights                         │
                                 │  seed.py заполняет таблицу flights при старте   │
                                 └──────────────────────────────────────────────────┘
                                                        │
                                 ┌──────────────────────▼──────────────────────────┐
                                 │  PostgreSQL :5432                                │
                                 │  ├── users    (auth-service)                    │
                                 │  ├── flights  (passenger-service)               │
                                 │  └── results  (analysis-service)                │
                                 └─────────────────────────────────────────────────┘
```

### ML-пайплайн (POST /analysis)

| Шаг | Что происходит |
|-----|----------------|
| 1 | Получаем всех пассажиров с их рейсами из passenger-service |
| 2 | Каждый пассажир сериализуется в текст: `"Passenger: male, age 34. Flights: SVO to AER, business class, ..."` |
| 3 | Sentence Transformer `all-MiniLM-L6-v2` строит эмбеддинги батчем |
| 4 | KMeans разбивает пассажиров на кластеры (n=5 по умолчанию) |
| 5 | UMAP сжимает эмбеддинги до 2D-координат для визуализации |
| 6 | Результаты сохраняются в БД (upsert по `profile_id`) |

---

## Стек

| Слой | Технология |
|------|------------|
| Runtime | Python 3.11 |
| Web framework | FastAPI + Uvicorn |
| ORM / БД | SQLAlchemy (async) + PostgreSQL 16 |
| ML | Sentence Transformers, scikit-learn (KMeans), umap-learn |
| Auth | PyJWT + bcrypt |
| Inter-service | httpx (async) |
| Тесты | pytest + pytest-asyncio |
| Контейнеризация | Docker + Docker Compose |
| Frontend | Vanilla JS + Chart.js |

---

## Структура проекта

```
s7_backend_project/
├── docker-compose.yml          # оркестрация всех сервисов
├── .env                        # секреты (не в git)
├── .env.example                # шаблон переменных окружения
│
├── frontend/
│   └── index.html              # SPA: логин, таблица, scatter plot
│
└── services/
    ├── auth-service/           # :8001 — регистрация и JWT
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── requirements-test.txt
    │   ├── pytest.ini
    │   ├── app/
    │   │   ├── main.py         # FastAPI app + lifespan
    │   │   ├── config.py       # Pydantic Settings
    │   │   ├── database.py     # async engine + session
    │   │   ├── models.py       # SQLAlchemy: User
    │   │   ├── schemas.py      # Pydantic I/O schemas
    │   │   ├── routes.py       # тонкие роутеры
    │   │   ├── service.py      # бизнес-логика
    │   │   ├── security.py     # JWT + bcrypt
    │   │   └── dependencies.py # get_db, get_current_user
    │   └── tests/
    │       ├── conftest.py
    │       └── test_auth.py
    │
    ├── passenger-service/      # internal — данные о рейсах
    │   ├── Dockerfile
    │   ├── seed.py             # генерация синтетических данных при старте
    │   ├── app/
    │   │   ├── main.py
    │   │   ├── config.py
    │   │   ├── database.py
    │   │   ├── models.py       # SQLAlchemy: flights (profile_id, gender, age, flights JSONB)
    │   │   ├── schemas.py
    │   │   ├── routes.py
    │   │   ├── service.py
    │   │   └── dependencies.py
    │   └── tests/
    │       ├── conftest.py
    │       └── test_passengers.py
    │
    └── analysis-service/       # :8003 — ML пайплайн
        ├── Dockerfile
        ├── app/
        │   ├── main.py         # FastAPI app + lifespan (загрузка ML моделей)
        │   ├── config.py
        │   ├── database.py
        │   ├── models.py       # SQLAlchemy: results
        │   ├── schemas.py
        │   ├── routes.py
        │   ├── ml_service.py   # сериализация, эмбеддинги, KMeans, UMAP
        │   └── dependencies.py
        └── tests/
            ├── conftest.py
            └── test_analysis.py
```

---

## Быстрый старт

### 1. Клонировать и настроить окружение

```bash
git clone <repo-url>
cd s7_backend_project
cp .env.example .env
```

Заполнить `.env` (см. раздел [Конфигурация](#конфигурация)).

### 2. Запустить

```bash
docker compose up --build
```

При первом запуске:
- Скачается модель `all-MiniLM-L6-v2` (~90 MB) — займёт время
- `seed.py` автоматически заполнит таблицу `flights` синтетическими данными

### 3. Открыть приложение

```
http://localhost:8080
```

Зарегистрировать аккаунт → нажать **Analyse** → получить scatter plot по кластерам.

---

## API

### auth-service `localhost:8001`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/register` | Регистрация нового аналитика |
| POST | `/auth/login` | Получить JWT-токен |
| GET | `/auth/me` | Данные текущего пользователя (требует `Bearer` токен) |

### analysis-service `localhost:8003`

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/analysis` | Запустить ML-пайплайн, сохранить и вернуть результаты |
| GET | `/analysis/results` | Прочитать сохранённые результаты из БД |

> **passenger-service** работает только во внутренней docker-сети и снаружи недоступен.

---

## Конфигурация

Скопируйте `.env.example` → `.env` и заполните значения:

```dotenv
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_PORT=5432
POSTGRES_DB=your_db

# Сгенерировать: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your_secret_key

AUTH_PORT=8001
ANALYSIS_PORT=8003
FRONTEND_PORT=8080

JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

ML-параметры задаются через env в `docker-compose.yml` или `analysis-service/app/config.py`:

| Переменная | Значение по умолчанию | Описание |
|------------|-----------------------|----------|
| `KMEANS_N_CLUSTERS` | `5` | Количество кластеров |
| `SENTENCE_TRANSFORMER_MODEL` | `all-MiniLM-L6-v2` | HuggingFace модель |

---

## Тесты

Тесты запускаются отдельно для каждого сервиса. Пример для auth-service:

```bash
cd services/auth-service
pip install -r requirements.txt -r requirements-test.txt
pytest --cov=app --cov-report=term-missing
```

Аналогично для `passenger-service` и `analysis-service`.

Цель покрытия — **90%** на собственном коде (ML-пайплайн покрывается smoke-тестом).

---

## Ограничения MVP

- JWT хранится в `localStorage` (уязвимо к XSS — допущение MVP)
- Один инстанс PostgreSQL на все сервисы (без изоляции БД)
- Нет защиты от одновременных вызовов `POST /analysis`
- Нет пагинации в `/passengers/flights`
- Нет Nginx, rate limiting, structured logging
